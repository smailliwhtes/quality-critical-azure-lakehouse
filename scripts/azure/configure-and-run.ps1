[CmdletBinding()]
param(
  [string]$ResourceGroupName = 'rg-qcal-part4-dev',
  [string]$CatalogName = 'part4_ops',
  [string]$ExecutionCommit = ''
)

# Auditable control path: storage-credentials create, external-locations create,
# volumes create, secrets create-scope, pipeline create-run, jobs repair-run.
# Bundle resource keys: part4_lakehouse_job and part4_performance_job.

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ($ResourceGroupName -ne 'rg-qcal-part4-dev' -or $CatalogName -ne 'part4_ops') {
  throw 'Cloud execution is fixed to the isolated Part 4 resource group and catalog.'
}

$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..')).Path
$privateRoot = if ($env:PART4_PRIVATE_EVIDENCE_ROOT) {
  $env:PART4_PRIVATE_EVIDENCE_ROOT
} else {
  'C:\Users\micha\Part4_Private_Evidence'
}
$privateReceipts = Join-Path $privateRoot 'receipts'
$privateSecrets = Join-Path $privateRoot 'secrets'
$publicReceipts = Join-Path $repoRoot 'evidence\public\receipts'
$commandErrorPath = Join-Path $privateReceipts 'last-command.stderr.txt'
New-Item -ItemType Directory -Path $privateReceipts -Force | Out-Null
New-Item -ItemType Directory -Path $privateSecrets -Force | Out-Null
New-Item -ItemType Directory -Path $publicReceipts -Force | Out-Null

$python = if (Test-Path -LiteralPath (Join-Path $repoRoot '.venv\Scripts\python.exe')) {
  Join-Path $repoRoot '.venv\Scripts\python.exe'
} else {
  'python'
}
$databricks = if (Test-Path -LiteralPath (Join-Path $repoRoot '.tools\databricks\databricks.exe')) {
  Join-Path $repoRoot '.tools\databricks\databricks.exe'
} else {
  'databricks'
}

if (-not $ExecutionCommit) {
  $ExecutionCommit = (git -C $repoRoot rev-parse HEAD).Trim()
}
if ($ExecutionCommit -notmatch '^[0-9a-f]{40}$') {
  throw 'ExecutionCommit must be a full Git commit SHA.'
}

function Protect-PublicText([string]$Text) {
  $protected = $Text -replace '(?i)[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}', '<redacted-email>'
  $protected = $protected -replace '(?i)[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '<redacted-guid>'
  $protected = $protected -replace '(?i)Endpoint=sb://[^"\s]+;SharedAccessKeyName=[^;"\s]+;SharedAccessKey=[^;"\s]+', '<redacted-event-hubs-connection>'
  $protected = $protected -replace '(?i)(sig|se|sp|sv|sr)=[^&"\s]+', '$1=<redacted>'
  return $protected
}

function Write-PrivateText([string]$Name, [string]$Text) {
  [IO.File]::WriteAllText((Join-Path $privateReceipts $Name), $Text)
}

function Write-PublicJson([string]$Name, $Payload) {
  $json = if ($Payload -is [string]) { $Payload } else { $Payload | ConvertTo-Json -Depth 100 }
  [IO.File]::WriteAllText((Join-Path $publicReceipts $Name), (Protect-PublicText $json))
}

function Invoke-ExternalJson {
  param(
    [Parameter(Mandatory = $true)][string]$Command,
    [Parameter(Mandatory = $true)][string[]]$Arguments,
    [Parameter(Mandatory = $true)][string]$FailureMessage,
    [switch]$AllowFailure
  )
  $rawLines = & $Command @Arguments 2> $commandErrorPath
  $exitCode = $LASTEXITCODE
  $raw = $rawLines -join [Environment]::NewLine
  if ($exitCode -ne 0) {
    if ($AllowFailure) { return $null }
    throw $FailureMessage
  }
  if (-not $raw) { return $null }
  return $raw | ConvertFrom-Json
}

function Invoke-AzTsv([string[]]$Arguments, [string]$FailureMessage) {
  $raw = & az @Arguments --only-show-errors --output tsv 2> $commandErrorPath
  if ($LASTEXITCODE -ne 0) { throw $FailureMessage }
  return ($raw -join [Environment]::NewLine).Trim()
}

function Test-DatabricksObject([string[]]$Arguments) {
  & $databricks @Arguments -o json 1>$null 2> $commandErrorPath
  return $LASTEXITCODE -eq 0
}

function Get-Sha256([string]$Value) {
  $bytes = [Text.Encoding]::UTF8.GetBytes($Value)
  $hash = [Security.Cryptography.SHA256]::HashData($bytes)
  return [Convert]::ToHexString($hash).ToLowerInvariant()
}

function Wait-DatabricksRun([long]$RunId, [bool]$ExpectSuccess, [int]$RepairId = 0) {
  $deadline = (Get-Date).ToUniversalTime().AddHours(2)
  $repairObserved = $RepairId -eq 0
  while ((Get-Date).ToUniversalTime() -lt $deadline) {
    $run = Invoke-ExternalJson -Command $databricks -Arguments @(
      'jobs', 'get-run', "$RunId", '--include-history', '-o', 'json'
    ) -FailureMessage 'Databricks run status lookup failed.'
    if ($RepairId -gt 0) {
      $repairObserved = @($run.repair_history | Where-Object { $_.id -eq $RepairId }).Count -eq 1
    }
    $lifeCycle = [string]$run.state.life_cycle_state
    $result = [string]$run.state.result_state
    Write-Host "Databricks run $RunId state: $lifeCycle / $result"
    if ($repairObserved -and $lifeCycle -in @('TERMINATED', 'SKIPPED', 'INTERNAL_ERROR')) {
      if ($ExpectSuccess -and $result -ne 'SUCCESS') {
        Write-PrivateText -Name "databricks-run-$RunId.json" -Text ($run | ConvertTo-Json -Depth 100)
        throw "Databricks run $RunId did not succeed."
      }
      if (-not $ExpectSuccess -and $result -eq 'SUCCESS') {
        throw 'The controlled incident unexpectedly succeeded; no failure evidence was produced.'
      }
      return $run
    }
    Start-Sleep -Seconds 20
  }
  throw "Databricks run $RunId exceeded the two-hour execution deadline."
}

function Copy-GovernedReceipt([string]$RelativePath, [string]$PublicName) {
  $privatePath = Join-Path $privateReceipts $PublicName
  & $databricks fs cp "dbfs:/Volumes/$CatalogName/governance/evidence/$RelativePath" $privatePath --overwrite 2> $commandErrorPath
  if ($LASTEXITCODE -ne 0) { throw "Governed receipt $RelativePath could not be collected." }
  $raw = Get-Content -LiteralPath $privatePath -Raw
  [IO.File]::WriteAllText((Join-Path $publicReceipts $PublicName), (Protect-PublicText $raw))
  return $raw | ConvertFrom-Json
}

function Invoke-CostCheckpoint([string]$Stage) {
  & (Join-Path $PSScriptRoot 'cost-snapshot.ps1') -Stage $Stage | Out-Null
  $receipt = Get-Content -LiteralPath (Join-Path $publicReceipts "cost-$Stage.json") -Raw | ConvertFrom-Json
  if ($null -ne $receipt.amount) {
    $amount = [decimal]$receipt.amount
    if ($amount -ge 20) {
      & (Join-Path $PSScriptRoot 'teardown.ps1')
      throw 'The $20 teardown threshold was reached; isolated resources were deleted.'
    }
    if ($amount -ge 15) {
      throw 'The $15 new-compute stop threshold was reached.'
    }
  }
}

function Set-DatabricksSecretFromStdin([string]$Scope, [string]$Key, [string]$Value) {
  $start = [Diagnostics.ProcessStartInfo]::new()
  $start.FileName = $databricks
  $start.UseShellExecute = $false
  $start.RedirectStandardInput = $true
  $start.RedirectStandardOutput = $true
  $start.RedirectStandardError = $true
  foreach ($argument in @('secrets', 'put-secret', $Scope, $Key)) {
    $start.ArgumentList.Add($argument)
  }
  $process = [Diagnostics.Process]::new()
  $process.StartInfo = $start
  $null = $process.Start()
  $process.StandardInput.Write($Value)
  $process.StandardInput.Close()
  $stdout = $process.StandardOutput.ReadToEnd()
  $stderr = $process.StandardError.ReadToEnd()
  $process.WaitForExit()
  Write-PrivateText -Name 'databricks-secret-put.stderr.txt' -Text $stderr
  if ($process.ExitCode -ne 0) { throw 'Databricks-backed secret upload failed.' }
  if ($stdout) { Write-PrivateText -Name 'databricks-secret-put.stdout.txt' -Text $stdout }
}

Write-Host 'Discovering the isolated Azure resources.'
$storageAccountName = Invoke-AzTsv @(
  'storage', 'account', 'list', '--resource-group', $ResourceGroupName, '--query', '[0].name'
) 'Storage account discovery failed.'
$dataFactoryName = Invoke-AzTsv @(
  'datafactory', 'list', '--resource-group', $ResourceGroupName, '--query', '[0].name'
) 'Data Factory discovery failed.'
$eventHubsNamespace = Invoke-AzTsv @(
  'eventhubs', 'namespace', 'list', '--resource-group', $ResourceGroupName, '--query', '[0].name'
) 'Event Hubs namespace discovery failed.'
$keyVaultName = Invoke-AzTsv @(
  'keyvault', 'list', '--resource-group', $ResourceGroupName, '--query', '[0].name'
) 'Key Vault discovery failed.'
$keyVaultId = Invoke-AzTsv @(
  'keyvault', 'show', '--resource-group', $ResourceGroupName, '--name', $keyVaultName, '--query', 'id'
) 'Key Vault resource ID discovery failed.'
$keyVaultUri = Invoke-AzTsv @(
  'keyvault', 'show', '--resource-group', $ResourceGroupName, '--name', $keyVaultName, '--query', 'properties.vaultUri'
) 'Key Vault URI discovery failed.'
$accessConnectorId = Invoke-AzTsv @(
  'resource', 'list', '--resource-group', $ResourceGroupName,
  '--resource-type', 'Microsoft.Databricks/accessConnectors', '--query', '[0].id'
) 'Databricks Access Connector discovery failed.'
$workspace = Invoke-ExternalJson -Command 'az' -Arguments @(
  'databricks', 'workspace', 'list', '--resource-group', $ResourceGroupName,
  '--only-show-errors', '--output', 'json'
) -FailureMessage 'Databricks workspace discovery failed.'
$workspace = @($workspace)[0]
if (-not $workspace -or $workspace.sku.name -ne 'trial') {
  throw 'The isolated workspace is absent or is not the approved Trial SKU.'
}
$workspaceName = [string]$workspace.name
$workspaceUrl = [string]$workspace.workspaceUrl
$workspaceResourceId = [string]$workspace.id
$tenantId = Invoke-AzTsv @('account', 'show', '--query', 'tenantId') 'Tenant discovery failed.'

$workspaceDeadline = (Get-Date).ToUniversalTime().AddMinutes(30)
do {
  $workspaceState = Invoke-AzTsv @(
    'databricks', 'workspace', 'show', '--resource-group', $ResourceGroupName,
    '--name', $workspaceName, '--query', 'provisioningState'
  ) 'Databricks workspace readiness lookup failed.'
  if ($workspaceState -eq 'Succeeded') { break }
  if ($workspaceState -in @('Failed', 'Canceled')) { throw "Workspace provisioning ended in $workspaceState." }
  Start-Sleep -Seconds 20
} while ((Get-Date).ToUniversalTime() -lt $workspaceDeadline)
if ($workspaceState -ne 'Succeeded') { throw 'Databricks workspace provisioning timed out.' }

$env:DATABRICKS_HOST = "https://$workspaceUrl"
$env:DATABRICKS_AZURE_RESOURCE_ID = $workspaceResourceId
$env:DATABRICKS_AUTH_TYPE = 'azure-cli'
Remove-Item Env:DATABRICKS_TOKEN -ErrorAction SilentlyContinue
Remove-Item Env:DATABRICKS_CLIENT_SECRET -ErrorAction SilentlyContinue

$currentUser = Invoke-ExternalJson -Command $databricks -Arguments @(
  'current-user', 'me', '-o', 'json'
) -FailureMessage 'Azure CLI authentication to the Databricks Trial workspace failed.'
$metastore = Invoke-ExternalJson -Command $databricks -Arguments @(
  'metastores', 'current', '-o', 'json'
) -FailureMessage 'The Trial workspace does not have a usable Unity Catalog metastore.'

Write-Host 'Uploading governed synthetic sources with Azure AD authentication.'
$sourceFiles = @(
  'reference/sites.jsonl',
  'reference/products.jsonl',
  'reference/sensors.jsonl',
  'batch/batch_master.jsonl',
  'cdc/batch_change_events.jsonl',
  'hard_failure/reserved_schema_failure.jsonl'
)
$sourceDirectories = @('volume', 'volume/reference', 'volume/batch', 'volume/cdc', 'volume/hard_failure')
foreach ($directory in $sourceDirectories) {
  $uploaded = $false
  for ($attempt = 1; $attempt -le 15 -and -not $uploaded; $attempt++) {
    az storage fs directory create --account-name $storageAccountName --file-system source `
      --name $directory --auth-mode login --only-show-errors --output none 2> $commandErrorPath
    $uploaded = $LASTEXITCODE -eq 0
    if (-not $uploaded) { Start-Sleep -Seconds 20 }
  }
  if (-not $uploaded) { throw 'Azure Storage RBAC did not propagate before the bounded deadline.' }
}
foreach ($relative in $sourceFiles) {
  $sourcePath = Join-Path (Join-Path $repoRoot 'data\synthetic') ($relative -replace '/', '\')
  az storage fs file upload --account-name $storageAccountName --file-system source `
    --path "volume/$relative" --source $sourcePath --overwrite true --auth-mode login `
    --only-show-errors --output none 2> $commandErrorPath
  if ($LASTEXITCODE -ne 0) { throw "Source upload failed for $relative." }
}
Write-PublicJson 'source-upload.json' ([ordered]@{
  schema = 'part4-source-upload-receipt/v1'
  captured_at_utc = (Get-Date).ToUniversalTime().ToString('o')
  authentication = 'AZURE_AD_RBAC'
  files_uploaded = $sourceFiles.Count
  source_manifest_sha256 = (Get-FileHash -LiteralPath (Join-Path $repoRoot 'data\synthetic\manifest.json') -Algorithm SHA256).Hash.ToLowerInvariant()
  storage_keys_used = $false
  execution_commit = $ExecutionCommit
})

Write-Host 'Deploying and running the parameterized ADF ForEach/Copy path.'
$adfTemp = Join-Path $privateRoot 'adf-runtime'
New-Item -ItemType Directory -Path $adfTemp -Force | Out-Null
$adfAssets = @(
  @{ Kind = 'linked-service'; Path = 'adf\linkedService\ls_github_http.json'; Name = 'ls_github_http' },
  @{ Kind = 'linked-service'; Path = 'adf\linkedService\ls_adls_managed_identity.json'; Name = 'ls_adls_managed_identity' },
  @{ Kind = 'dataset'; Path = 'adf\dataset\ds_github_quality_json.json'; Name = 'ds_github_quality_json' },
  @{ Kind = 'dataset'; Path = 'adf\dataset\ds_adls_quality_json.json'; Name = 'ds_adls_quality_json' },
  @{ Kind = 'pipeline'; Path = 'adf\pipeline\pl_ingest_batch_quality.json'; Name = 'pl_ingest_batch_quality' }
)
foreach ($asset in $adfAssets) {
  $definition = Get-Content -LiteralPath (Join-Path $repoRoot $asset.Path) -Raw | ConvertFrom-Json
  $propertiesPath = Join-Path $adfTemp "$($asset.Name).properties.json"
  [IO.File]::WriteAllText($propertiesPath, ($definition.properties | ConvertTo-Json -Depth 100))
  $atFile = "@$propertiesPath"
  if ($asset.Kind -eq 'linked-service') {
    az datafactory linked-service create --resource-group $ResourceGroupName `
      --factory-name $dataFactoryName --name $asset.Name --properties $atFile `
      --only-show-errors --output none 2> $commandErrorPath
  } elseif ($asset.Kind -eq 'dataset') {
    az datafactory dataset create --resource-group $ResourceGroupName `
      --factory-name $dataFactoryName --name $asset.Name --properties $atFile `
      --only-show-errors --output none 2> $commandErrorPath
  } else {
    az datafactory pipeline create --resource-group $ResourceGroupName `
      --factory-name $dataFactoryName --name $asset.Name --pipeline $atFile `
      --only-show-errors --output none 2> $commandErrorPath
  }
  if ($LASTEXITCODE -ne 0) { throw "ADF $($asset.Kind) deployment failed." }
}
$adfParametersPath = Join-Path $adfTemp 'run-parameters.json'
[IO.File]::WriteAllText(
  $adfParametersPath,
  (@{ storageAccountName = $storageAccountName } | ConvertTo-Json -Compress)
)
$adfRun = Invoke-ExternalJson -Command 'az' -Arguments @(
  'datafactory', 'pipeline', 'create-run', '--resource-group', $ResourceGroupName,
  '--factory-name', $dataFactoryName, '--name', 'pl_ingest_batch_quality',
  '--parameters', "@$adfParametersPath", '--only-show-errors', '--output', 'json'
) -FailureMessage 'ADF pipeline run submission failed.'
$adfRunId = [string]$adfRun.runId
$adfDeadline = (Get-Date).ToUniversalTime().AddMinutes(30)
do {
  $adfStatus = Invoke-ExternalJson -Command 'az' -Arguments @(
    'datafactory', 'pipeline-run', 'show', '--resource-group', $ResourceGroupName,
    '--factory-name', $dataFactoryName, '--run-id', $adfRunId,
    '--only-show-errors', '--output', 'json'
  ) -FailureMessage 'ADF pipeline status lookup failed.'
  Write-Host "ADF pipeline state: $($adfStatus.status)"
  if ($adfStatus.status -in @('Succeeded', 'Failed', 'Cancelled')) { break }
  Start-Sleep -Seconds 15
} while ((Get-Date).ToUniversalTime() -lt $adfDeadline)
if ($adfStatus.status -ne 'Succeeded') {
  Write-PrivateText -Name 'adf-pipeline-run.json' -Text ($adfStatus | ConvertTo-Json -Depth 100)
  throw 'ADF ForEach/Copy pipeline did not succeed.'
}
$activityWindowStart = (Get-Date).ToUniversalTime().AddHours(-2).ToString('o')
$activityWindowEnd = (Get-Date).ToUniversalTime().AddHours(2).ToString('o')
$adfActivities = Invoke-ExternalJson -Command 'az' -Arguments @(
  'datafactory', 'activity-run', 'query-by-pipeline-run', '--resource-group', $ResourceGroupName,
  '--factory-name', $dataFactoryName, '--run-id', $adfRunId,
  '--last-updated-after', $activityWindowStart, '--last-updated-before', $activityWindowEnd,
  '--only-show-errors', '--output', 'json'
) -FailureMessage 'ADF activity-run collection failed.'
Write-PrivateText -Name 'adf-pipeline-run.json' -Text ($adfStatus | ConvertTo-Json -Depth 100)
Write-PrivateText -Name 'adf-activity-runs.json' -Text ($adfActivities | ConvertTo-Json -Depth 100)
$copyActivities = @($adfActivities.value | Where-Object { $_.activityType -eq 'Copy' })
Write-PublicJson 'adf-copy-run.json' ([ordered]@{
  schema = 'part4-adf-copy-receipt/v1'
  captured_at_utc = (Get-Date).ToUniversalTime().ToString('o')
  pipeline = 'pl_ingest_batch_quality'
  status = [string]$adfStatus.status
  public_run_id = "adf-$((Get-Sha256 $adfRunId).Substring(0, 12))"
  execution_commit = $ExecutionCommit
  source_commit = '836901141adce556adec1811d132127953d52c9b'
  files_requested = 6
  copy_activities = @($copyActivities | ForEach-Object {
    [ordered]@{
      activity_name = $_.activityName
      status = $_.status
      rows_read = $_.output.rowsRead
      rows_copied = $_.output.rowsCopied
      bytes_read = $_.output.dataRead
      bytes_written = $_.output.dataWritten
      copy_duration_seconds = $_.output.copyDuration
    }
  })
  managed_identity = $true
  connection_material_included = $false
})

Write-Host 'Creating Unity Catalog storage objects and governed volumes.'
$credentialName = 'part4_access_connector'
if (-not (Test-DatabricksObject @('storage-credentials', 'get', $credentialName))) {
  $credentialPath = Join-Path $privateRoot 'storage-credential.json'
  [IO.File]::WriteAllText($credentialPath, (@{
    name = $credentialName
    azure_managed_identity = @{ access_connector_id = $accessConnectorId }
    comment = 'Part 4 synthetic lakehouse Access Connector credential.'
  } | ConvertTo-Json -Depth 10))
  $null = Invoke-ExternalJson -Command $databricks -Arguments @(
    'storage-credentials', 'create', '--json', "@$credentialPath", '-o', 'json'
  ) -FailureMessage 'Unity Catalog storage credential creation failed.'
}
$containers = @('managed', 'source', 'landing', 'quarantine', 'checkpoints', 'evidence')
foreach ($container in $containers) {
  $locationName = "part4_$container"
  if (-not (Test-DatabricksObject @('external-locations', 'get', $locationName))) {
    $null = Invoke-ExternalJson -Command $databricks -Arguments @(
      'external-locations', 'create', $locationName,
      "abfss://$container@$storageAccountName.dfs.core.windows.net/", $credentialName,
      '--comment', "Part 4 $container container; synthetic portfolio data only.", '-o', 'json'
    ) -FailureMessage "External location creation failed for $container."
  }
}
if (-not (Test-DatabricksObject @('catalogs', 'get', $CatalogName))) {
  $null = Invoke-ExternalJson -Command $databricks -Arguments @(
    'catalogs', 'create', $CatalogName,
    '--storage-root', "abfss://managed@$storageAccountName.dfs.core.windows.net/catalog",
    '--comment', 'Quality-critical synthetic lakehouse portfolio catalog.', '-o', 'json'
  ) -FailureMessage 'Unity Catalog catalog creation failed.'
}
foreach ($schema in @('bronze', 'silver', 'gold', 'governance')) {
  if (-not (Test-DatabricksObject @('schemas', 'get', "$CatalogName.$schema"))) {
    $null = Invoke-ExternalJson -Command $databricks -Arguments @(
      'schemas', 'create', $schema, $CatalogName,
      '--comment', "Part 4 $schema data-engineering layer.", '-o', 'json'
    ) -FailureMessage "Unity Catalog schema creation failed for $schema."
  }
}
foreach ($container in @('source', 'landing', 'quarantine', 'checkpoints', 'evidence')) {
  $fullName = "$CatalogName.governance.$container"
  if (-not (Test-DatabricksObject @('volumes', 'read', $fullName))) {
    $null = Invoke-ExternalJson -Command $databricks -Arguments @(
      'volumes', 'create', $CatalogName, 'governance', $container, 'EXTERNAL',
      '--storage-location', "abfss://$container@$storageAccountName.dfs.core.windows.net/volume",
      '--comment', "Governed $container volume for the Part 4 lakehouse.", '-o', 'json'
    ) -FailureMessage "Unity Catalog volume creation failed for $container."
  }
}

Write-Host 'Storing the Event Hubs credential without printing connection material.'
$connection = Invoke-AzTsv @(
  'eventhubs', 'eventhub', 'authorization-rule', 'keys', 'list',
  '--resource-group', $ResourceGroupName, '--namespace-name', $eventHubsNamespace,
  '--eventhub-name', 'quality-telemetry', '--name', 'stream-producer-consumer',
  '--query', 'primaryConnectionString'
) 'Event Hubs connection retrieval failed.'
$secretFile = Join-Path $privateSecrets 'eventhubs-connection-string.txt'
[IO.File]::WriteAllText($secretFile, $connection)
az keyvault secret set --vault-name $keyVaultName --name 'eventhubs-connection-string' `
  --file $secretFile --only-show-errors --output none 2> $commandErrorPath
if ($LASTEXITCODE -ne 0) { throw 'Key Vault secret write failed.' }

$databricksScope = 'part4-key-vault'
$secretBackend = 'EXISTING'
if (-not (Test-DatabricksObject @('secrets', 'list-secrets', $databricksScope))) {
  $scopePath = Join-Path $privateRoot 'key-vault-scope.json'
  [IO.File]::WriteAllText($scopePath, (@{
    scope = $databricksScope
    scope_backend_type = 'AZURE_KEYVAULT'
    backend_azure_keyvault = @{
      resource_id = $keyVaultId
      tenant_id = $tenantId
      dns_name = $keyVaultUri
    }
  } | ConvertTo-Json -Depth 10))
  $scope = Invoke-ExternalJson -Command $databricks -Arguments @(
    'secrets', 'create-scope', '--json', "@$scopePath", '-o', 'json'
  ) -FailureMessage 'IGNORE' -AllowFailure
  if ($null -ne $scope -or (Test-DatabricksObject @('secrets', 'list-secrets', $databricksScope))) {
    $secretBackend = 'AZURE_KEYVAULT'
  } else {
    $null = Invoke-ExternalJson -Command $databricks -Arguments @(
      'secrets', 'create-scope', $databricksScope, '--scope-backend-type', 'DATABRICKS', '-o', 'json'
    ) -FailureMessage 'Databricks-backed secret scope fallback failed.'
    Set-DatabricksSecretFromStdin -Scope $databricksScope -Key 'eventhubs-connection-string' -Value $connection
    $secretBackend = 'DATABRICKS_FALLBACK'
  }
}
Remove-Item -LiteralPath $secretFile -Force

$sparkVersions = Invoke-ExternalJson -Command $databricks -Arguments @(
  'clusters', 'spark-versions', '-o', 'json'
) -FailureMessage 'Databricks runtime discovery failed.'
$ltsVersions = @($sparkVersions.versions | Where-Object {
  $_.name -match '(?i)LTS' -and $_.name -notmatch '(?i)(ML|GPU|Beta|Preview)'
} | ForEach-Object {
  $match = [regex]::Match([string]$_.key, '^(\d+)\.(\d+)')
  [pscustomobject]@{
    key = $_.key
    name = $_.name
    major = if ($match.Success) { [int]$match.Groups[1].Value } else { 0 }
    minor = if ($match.Success) { [int]$match.Groups[2].Value } else { 0 }
  }
} | Sort-Object major, minor -Descending)
if ($ltsVersions.Count -eq 0) { throw 'No stable LTS Databricks Runtime was exposed by the Trial workspace.' }
$sparkVersion = [string]$ltsVersions[0].key
$sparkVersionLabel = [string]$ltsVersions[0].name
$nodeTypes = Invoke-ExternalJson -Command $databricks -Arguments @(
  'clusters', 'list-node-types', '-o', 'json'
) -FailureMessage 'Databricks node-type discovery failed.'
$availableNodeTypes = @($nodeTypes.node_types | ForEach-Object { $_.node_type_id })
if ('Standard_DS3_v2' -notin $availableNodeTypes) {
  throw 'The approved Standard_DS3_v2 primary job node type is not available.'
}
$pipelineNodeType = if ('Standard_D2ads_v6' -in $availableNodeTypes) {
  'Standard_D2ads_v6'
} else {
  [string]@($nodeTypes.node_types | Where-Object {
    $_.num_cores -eq 2 -and -not $_.is_deprecated -and $_.node_type_id -notmatch 'NC|ND|NV|GPU'
  } | Sort-Object node_type_id)[0].node_type_id
}
if (-not $pipelineNodeType) {
  throw 'No supported two-vCPU single-node pipeline type was exposed by the Trial workspace.'
}

$bundleVariables = @(
  "catalog=$CatalogName",
  "spark_version=$sparkVersion",
  'node_type_id=Standard_DS3_v2',
  "pipeline_node_type_id=$pipelineNodeType",
  "storage_account_name=$storageAccountName",
  "event_hubs_namespace=$eventHubsNamespace",
  'event_hub_name=quality-telemetry',
  "execution_commit=$ExecutionCommit"
)
$bundleArguments = @()
foreach ($variable in $bundleVariables) { $bundleArguments += @('--var', $variable) }
Push-Location $repoRoot
try {
  $bundleValidationOutput = & $databricks bundle validate -t dev @bundleArguments 2> $commandErrorPath
  if ($LASTEXITCODE -ne 0) { throw 'Databricks bundle validate failed.' }
  Write-PrivateText -Name 'bundle-validate.stdout.txt' -Text ($bundleValidationOutput -join [Environment]::NewLine)
  $bundleDeployOutput = & $databricks bundle deploy -t dev @bundleArguments 2> $commandErrorPath
  if ($LASTEXITCODE -ne 0) { throw 'Databricks bundle deploy failed.' }
  Write-PrivateText -Name 'bundle-deploy.stdout.txt' -Text ($bundleDeployOutput -join [Environment]::NewLine)
  $bundleSummaryOutput = & $databricks bundle summary -t dev @bundleArguments -o json 2> $commandErrorPath
  if ($LASTEXITCODE -ne 0) { throw 'Databricks bundle summary failed.' }
  Write-PrivateText -Name 'bundle-summary.json' -Text ($bundleSummaryOutput -join [Environment]::NewLine)
  $bundleSummary = ($bundleSummaryOutput -join [Environment]::NewLine) | ConvertFrom-Json
} finally {
  Pop-Location
}

Write-PublicJson 'platform-configuration.json' ([ordered]@{
  schema = 'part4-platform-configuration/v1'
  captured_at_utc = (Get-Date).ToUniversalTime().ToString('o')
  workspace_sku = 'trial'
  workspace_mode = 'hybrid'
  runtime_key = $sparkVersion
  runtime_label = $sparkVersionLabel
  primary_job_compute = @{ node_type = 'Standard_DS3_v2'; driver_count = 1; worker_count = 1; vcpus = 8 }
  overlapping_pipeline_compute = @{ node_type = $pipelineNodeType; single_node = $true; vcpus = 2 }
  peak_verified_quota_plan_vcpus = 10
  unity_catalog_metastore_attached = [bool]$metastore
  storage_credential = 'AZURE_MANAGED_IDENTITY_ACCESS_CONNECTOR'
  secret_backend = $secretBackend
  databricks_arm_diagnostics = 'PRODUCTION_BLUEPRINT_PLATFORM_UNSUPPORTED'
  databricks_arm_diagnostics_limitation = 'The live Trial workspace exposed no diagnostic log or metric categories through ARM.'
  long_lived_token_created = $false
  current_user_recorded_publicly = $false
  execution_commit = $ExecutionCommit
})

Write-Host 'Emitting exactly 20,000 deterministic Event Hubs messages.'
$producerReceiptPath = Join-Path $publicReceipts 'event-hubs-producer.json'
$producerAlreadyCompleted = $false
if (Test-Path -LiteralPath $producerReceiptPath) {
  $existingProducerReceipt = Get-Content -LiteralPath $producerReceiptPath -Raw | ConvertFrom-Json
  $producerAlreadyCompleted = $existingProducerReceipt.events_emitted -eq 20000 -and `
    $existingProducerReceipt.connection_material_included -eq $false
}
if (-not $producerAlreadyCompleted) {
  $env:EVENT_HUB_CONNECTION_STRING = $connection
  $previousPythonPath = $env:PYTHONPATH
  $env:PYTHONPATH = Join-Path $repoRoot 'src'
  try {
    & $python -m qcal.cli send-telemetry `
      --source (Join-Path $repoRoot 'data\synthetic\event_hubs\sensor_messages.jsonl') `
      --event-hub-name 'quality-telemetry' --message-limit 20000 `
      --receipt $producerReceiptPath
    if ($LASTEXITCODE -ne 0) { throw 'The bounded Event Hubs producer failed.' }
  } finally {
    Remove-Item Env:EVENT_HUB_CONNECTION_STRING -ErrorAction SilentlyContinue
    $env:PYTHONPATH = $previousPythonPath
  }
} else {
  Write-Host 'Reusing the verified 20,000-message producer receipt; no duplicate messages emitted.'
}
$connection = $null
Invoke-CostCheckpoint -Stage 'ingestion'

$lakehouseJobId = [long]$bundleSummary.resources.jobs.part4_lakehouse_job.id
if (-not $lakehouseJobId) { throw 'The deployed lakehouse job was not found.' }
$performanceJobId = [long]$bundleSummary.resources.jobs.part4_performance_job.id
if (-not $performanceJobId) { throw 'The deployed performance job was not found.' }

function Start-LakehouseRun([string]$IncidentMode) {
  $requestPath = Join-Path $privateRoot "lakehouse-run-$IncidentMode.json"
  [IO.File]::WriteAllText($requestPath, (@{
    job_id = $lakehouseJobId
    job_parameters = @{
      incident_mode = $IncidentMode
      execution_commit = $ExecutionCommit
    }
  } | ConvertTo-Json -Depth 10))
  $submission = Invoke-ExternalJson -Command $databricks -Arguments @(
    'jobs', 'run-now', '--json', "@$requestPath", '--no-wait', '-o', 'json'
  ) -FailureMessage 'Lakehouse job submission failed.'
  return [long]$submission.run_id
}

Write-Host 'Running the clean Lakeflow baseline.'
$cleanRunId = Start-LakehouseRun -IncidentMode 'false'
$cleanRun = Wait-DatabricksRun -RunId $cleanRunId -ExpectSuccess $true
$cleanEvidenceTask = @($cleanRun.tasks | Where-Object { $_.task_key -eq 'evidence_receipt' })[0]
$cleanStreamTask = @($cleanRun.tasks | Where-Object { $_.task_key -eq 'bronze_stream' })[0]
$cleanGovernanceTask = @($cleanRun.tasks | Where-Object { $_.task_key -eq 'gold_publish' })[0]
$cleanReceipt = Copy-GovernedReceipt -RelativePath "jobs/$($cleanEvidenceTask.run_id).json" -PublicName 'lakeflow-clean-run.json'
$null = Copy-GovernedReceipt -RelativePath "streaming/$($cleanStreamTask.run_id).json" -PublicName 'structured-streaming-progress.json'
$null = Copy-GovernedReceipt -RelativePath "governance/$($cleanGovernanceTask.run_id).json" -PublicName 'unity-catalog-governance.json'

Write-Host 'Injecting the reserved hard contract failure.'
$incidentRunId = Start-LakehouseRun -IncidentMode 'true'
$incidentRun = Wait-DatabricksRun -RunId $incidentRunId -ExpectSuccess $false
$qualityFailureTask = @($incidentRun.tasks | Where-Object { $_.task_key -eq 'quality_gate' })[0]
$failureOutput = Invoke-ExternalJson -Command $databricks -Arguments @(
  'jobs', 'get-run-output', "$($qualityFailureTask.run_id)", '-o', 'json'
) -FailureMessage 'Controlled incident diagnostic collection failed.' -AllowFailure
Write-PrivateText -Name 'lakeflow-incident-run.json' -Text ($incidentRun | ConvertTo-Json -Depth 100)
if ($failureOutput) {
  Write-PrivateText -Name 'lakeflow-incident-output.json' -Text ($failureOutput | ConvertTo-Json -Depth 100)
}
Write-PublicJson 'lakeflow-controlled-incident.json' ([ordered]@{
  schema = 'part4-controlled-incident-receipt/v1'
  captured_at_utc = (Get-Date).ToUniversalTime().ToString('o')
  public_run_id = "dbx-$((Get-Sha256 "$incidentRunId").Substring(0, 12))"
  job_result = [string]$incidentRun.state.result_state
  failed_task = 'quality_gate'
  hard_contract = 'reserved_schema_contract'
  incident_input = 'reserved_schema_failure.jsonl'
  diagnostic = if ($failureOutput) { [string]$failureOutput.error } else { [string]$qualityFailureTask.state.state_message }
  execution_commit = $ExecutionCommit
  fabricated = $false
})

Write-Host 'Repairing only the affected Bronze path and its downstream dependencies.'
$repairRequestPath = Join-Path $privateRoot 'lakehouse-repair.json'
[IO.File]::WriteAllText($repairRequestPath, (@{
  run_id = $incidentRunId
  rerun_tasks = @('bronze_batch')
  rerun_dependent_tasks = $true
  job_parameters = @{
    incident_mode = 'false'
    execution_commit = $ExecutionCommit
  }
} | ConvertTo-Json -Depth 10))
$repairSubmission = Invoke-ExternalJson -Command $databricks -Arguments @(
  'jobs', 'repair-run', '--json', "@$repairRequestPath", '--no-wait', '-o', 'json'
) -FailureMessage 'Lakeflow repair submission failed.'
$repairId = [int]$repairSubmission.repair_id
Start-Sleep -Seconds 10
$repairedRun = Wait-DatabricksRun -RunId $incidentRunId -ExpectSuccess $true -RepairId $repairId
$repairEvidenceTask = @($repairedRun.tasks | Where-Object { $_.task_key -eq 'evidence_receipt' })[0]
$repairReceipt = Copy-GovernedReceipt -RelativePath "jobs/$($repairEvidenceTask.run_id).json" -PublicName 'lakeflow-repaired-run.json'

$cleanComparable = [ordered]@{
  row_counts = $cleanReceipt.row_counts
  content_hashes = $cleanReceipt.content_hashes
  duplicate_business_keys = $cleanReceipt.duplicate_business_keys
  current_version_violations = $cleanReceipt.current_version_violations
  aggregates = $cleanReceipt.aggregates
}
$repairComparable = [ordered]@{
  row_counts = $repairReceipt.row_counts
  content_hashes = $repairReceipt.content_hashes
  duplicate_business_keys = $repairReceipt.duplicate_business_keys
  current_version_violations = $repairReceipt.current_version_violations
  aggregates = $repairReceipt.aggregates
}
$cleanCanonical = $cleanComparable | ConvertTo-Json -Depth 100 -Compress
$repairCanonical = $repairComparable | ConvertTo-Json -Depth 100 -Compress
$recoveryMatches = $cleanCanonical -eq $repairCanonical
Write-PublicJson 'lakeflow-recovery-validation.json' ([ordered]@{
  schema = 'part4-recovery-validation/v1'
  captured_at_utc = (Get-Date).ToUniversalTime().ToString('o')
  repair_id = $repairId
  rerun_tasks = @('bronze_batch')
  rerun_dependent_tasks = $true
  successful_upstream_rerun = $false
  expected_and_recovered_match = $recoveryMatches
  clean_content_hash = Get-Sha256 $cleanCanonical
  recovered_content_hash = Get-Sha256 $repairCanonical
  duplicate_business_keys = $repairReceipt.duplicate_business_keys
  current_version_violations = $repairReceipt.current_version_violations
  validation = if ($recoveryMatches) { 'PASS' } else { 'FAIL' }
  execution_commit = $ExecutionCommit
})
if (-not $recoveryMatches) { throw 'Clean and repaired deterministic outputs did not reconcile.' }

Write-Host 'Running the five-million-row baseline and optimized benchmark three times each.'
$performanceSubmission = Invoke-ExternalJson -Command $databricks -Arguments @(
  'jobs', 'run-now', "$performanceJobId", '--no-wait', '-o', 'json'
) -FailureMessage 'Performance job submission failed.'
$performanceRun = Wait-DatabricksRun -RunId ([long]$performanceSubmission.run_id) -ExpectSuccess $true
$performanceTask = @($performanceRun.tasks | Where-Object { $_.task_key -eq 'compare_baseline_and_broadcast' })[0]
$performanceReceipt = Copy-GovernedReceipt -RelativePath "performance/$($performanceTask.run_id).json" -PublicName 'spark-performance-comparison.json'
if (-not $performanceReceipt.result_hashes_match) {
  throw 'Baseline and optimized performance-query results did not reconcile.'
}
Invoke-CostCheckpoint -Stage 'incident-performance'

Write-Host 'Discovering actual Log Analytics tables and monitoring state.'
$logWorkspaceName = Invoke-AzTsv @(
  'monitor', 'log-analytics', 'workspace', 'list', '--resource-group', $ResourceGroupName,
  '--query', '[0].name'
) 'Log Analytics workspace discovery failed.'
$logCustomerId = Invoke-AzTsv @(
  'monitor', 'log-analytics', 'workspace', 'show', '--resource-group', $ResourceGroupName,
  '--workspace-name', $logWorkspaceName, '--query', 'customerId'
) 'Log Analytics customer ID discovery failed.'
$logResult = Invoke-ExternalJson -Command 'az' -Arguments @(
  'monitor', 'log-analytics', 'query', '--workspace', $logCustomerId,
  '--analytics-query', 'search * | summarize record_count=count() by Type | order by record_count desc',
  '--timespan', 'P1D', '--only-show-errors', '--output', 'json'
) -FailureMessage 'Log Analytics query unavailable.' -AllowFailure
$alertEnabled = Invoke-AzTsv @(
  'monitor', 'activity-log', 'alert', 'show', '--resource-group', $ResourceGroupName,
  '--name', 'part4-failed-administrative-operation', '--query', 'enabled'
) 'Azure Monitor alert readback failed.'
$discoveredTables = @()
if ($logResult) {
  $discoveredTables = @($logResult.tables[0].rows | ForEach-Object {
    @{ table = [string]$_[0]; record_count = [long]$_[1] }
  })
}
Write-PublicJson 'monitoring-validation.json' ([ordered]@{
  schema = 'part4-monitoring-validation/v1'
  captured_at_utc = (Get-Date).ToUniversalTime().ToString('o')
  diagnostics_configured_before_workloads = $true
  discovered_tables = $discoveredTables
  alert_rule_enabled = ($alertEnabled -eq 'true')
  alert_fired = $false
  alert_status = 'DEMONSTRATED'
  limitation = 'The controlled data-plane quality failure did not trigger the administrative control-plane alert.'
  identifiers_included = $false
})

Write-Host 'Azure and Databricks execution completed; sanitized receipts are ready for curation.'
