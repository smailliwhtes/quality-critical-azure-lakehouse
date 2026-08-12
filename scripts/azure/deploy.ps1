[CmdletBinding()]
param(
  [string]$Location = 'eastus2',
  [string]$ResourceGroupName = 'rg-qcal-part4-dev',
  [string]$CurrentCostUsd = '0'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..')).Path
$privateRoot = if ($env:PART4_PRIVATE_EVIDENCE_ROOT) {
  $env:PART4_PRIVATE_EVIDENCE_ROOT
} elseif ($env:RUNNER_TEMP) {
  Join-Path $env:RUNNER_TEMP 'Part4_Private_Evidence'
} else {
  'C:\Users\micha\Part4_Private_Evidence'
}
$privateReceipts = Join-Path $privateRoot 'receipts'
$publicReceipts = Join-Path $repoRoot 'evidence\public\receipts'
New-Item -ItemType Directory -Path $privateReceipts -Force | Out-Null
New-Item -ItemType Directory -Path $publicReceipts -Force | Out-Null

$budgetRaw = if ($env:PART4_BUDGET_USD) { $env:PART4_BUDGET_USD } else { '20' }
$budgetValue = 0
if (-not [int]::TryParse($budgetRaw, [ref]$budgetValue) -or $budgetValue -le 0) {
  throw 'PART4_BUDGET_USD must be a positive integer.'
}

$python = if (Test-Path -LiteralPath (Join-Path $repoRoot '.venv\Scripts\python.exe')) {
  Join-Path $repoRoot '.venv\Scripts\python.exe'
} else {
  'python'
}
$previousPythonPath = $env:PYTHONPATH
$env:PYTHONPATH = Join-Path $repoRoot 'src'
try {
  & $python -m qcal.cli cost-gate --current-cost $CurrentCostUsd --budget $budgetRaw | Out-Null
  if ($LASTEXITCODE -ne 0) { throw 'Cost gate denied new cloud work.' }
} finally {
  $env:PYTHONPATH = $previousPythonPath
}

if ($Location -ne 'eastus2' -or $ResourceGroupName -ne 'rg-qcal-part4-dev') {
  throw 'This bounded deployment accepts only eastus2 and rg-qcal-part4-dev.'
}

$providers = @(
  'Microsoft.Authorization',
  'Microsoft.Consumption',
  'Microsoft.DataFactory',
  'Microsoft.Databricks',
  'Microsoft.EventHub',
  'Microsoft.Insights',
  'Microsoft.KeyVault',
  'Microsoft.ManagedIdentity',
  'Microsoft.OperationalInsights',
  'Microsoft.Storage'
)
foreach ($provider in $providers) {
  az provider register --namespace $provider --wait --output none
}

$deployerObjectId = ''
try {
  $deployerObjectId = (az ad signed-in-user show --query id --output tsv 2>$null).Trim()
} catch {
  $deployerObjectId = ''
}

$databricksServicePrincipalObjectId = ''
try {
  $databricksServicePrincipalObjectId = (
    az ad sp show --id '2ff814a6-3304-4ab8-85cb-cd0e6f879c1d' --query id --output tsv 2>$null
  ).Trim()
} catch {
  $databricksServicePrincipalObjectId = ''
}

function Protect-PublicText([string]$Text) {
  $protected = $Text -replace '(?i)[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}', '<redacted-email>'
  $protected = $protected -replace '(?i)[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '<redacted-guid>'
  return $protected
}

$template = Join-Path $repoRoot 'infra\main.bicep'
$parameters = Join-Path $repoRoot 'infra\params\dev.bicepparam'
$deploymentName = 'part4-' + (Get-Date).ToUniversalTime().ToString('yyyyMMdd-HHmmss')
$commonArguments = @(
  '--location', $Location,
  '--template-file', $template,
  '--parameters', $parameters,
  "PART4_BUDGET_USD=$budgetValue",
  "deployerObjectId=$deployerObjectId",
  "databricksServicePrincipalObjectId=$databricksServicePrincipalObjectId"
)

az bicep build --file $template --outfile (Join-Path $privateReceipts 'main.compiled.json')
az deployment sub validate --name "$deploymentName-validate" @commonArguments --output none

$whatIfRaw = az deployment sub what-if --name "$deploymentName-whatif" @commonArguments --result-format FullResourcePayloads --no-pretty-print --output json
if ($LASTEXITCODE -ne 0) { throw 'Subscription what-if failed.' }
[IO.File]::WriteAllText((Join-Path $privateReceipts 'bicep-what-if.raw.json'), $whatIfRaw)
[IO.File]::WriteAllText(
  (Join-Path $publicReceipts 'bicep-what-if.json'),
  (Protect-PublicText $whatIfRaw)
)

$expectedTypes = (Get-Content -LiteralPath (Join-Path $repoRoot 'infra\expected_resource_types.json') -Raw | ConvertFrom-Json).resource_types
$whatIf = $whatIfRaw | ConvertFrom-Json
$whatIfChanges = if ($whatIf.PSObject.Properties.Name -contains 'changes') {
  @($whatIf.changes)
} elseif (
  $whatIf.PSObject.Properties.Name -contains 'properties' -and
  $whatIf.properties.PSObject.Properties.Name -contains 'changes'
) {
  @($whatIf.properties.changes)
} else {
  throw 'Subscription what-if response did not contain a recognized changes collection.'
}
$destructiveChanges = @($whatIfChanges | Where-Object { $_.changeType -eq 'Delete' })
if ($destructiveChanges.Count -gt 0) {
  throw 'Subscription what-if contains a destructive deletion; deployment stopped.'
}
$actualTypes = @($whatIfChanges | ForEach-Object {
  if ($null -ne $_.after -and $_.after.PSObject.Properties.Name -contains 'type') {
    $_.after.type
  } elseif ($null -ne $_.before -and $_.before.PSObject.Properties.Name -contains 'type') {
    $_.before.type
  }
} | Where-Object { $_ } | Sort-Object -Unique)
$unexpected = @($actualTypes | Where-Object { $_ -and $_ -notin $expectedTypes })
if ($unexpected.Count -gt 0) {
  throw "What-if contains unexpected resource types: $($unexpected -join ', ')"
}

$deploymentRaw = az deployment sub create --name $deploymentName @commonArguments --output json
if ($LASTEXITCODE -ne 0) { throw 'Subscription deployment failed.' }
[IO.File]::WriteAllText((Join-Path $privateReceipts 'deployment.raw.json'), $deploymentRaw)
[IO.File]::WriteAllText(
  (Join-Path $publicReceipts 'infrastructure-deployment.json'),
  (Protect-PublicText $deploymentRaw)
)

$workspaceName = (az databricks workspace list --resource-group $ResourceGroupName --query '[0].name' --output tsv).Trim()
$workspaceSku = (az databricks workspace show --resource-group $ResourceGroupName --name $workspaceName --query 'sku.name' --output tsv).Trim()
if ($workspaceSku -ne 'trial') {
  az group delete --name $ResourceGroupName --yes --no-wait
  throw "Databricks workspace did not reconcile to Trial. Teardown started. Observed SKU: $workspaceSku"
}

$inventory = az resource list --resource-group $ResourceGroupName --query '[].{name:name,type:type,location:location,kind:kind,sku:sku.name,tags:tags}' --output json
[IO.File]::WriteAllText((Join-Path $publicReceipts 'resource-inventory.json'), (Protect-PublicText $inventory))
[IO.File]::WriteAllText(
  (Join-Path $publicReceipts 'trial-gate.json'),
  (@{
    schema = 'part4-trial-gate/v1'
    captured_at_utc = (Get-Date).ToUniversalTime().ToString('o')
    location = $Location
    workspace_sku = $workspaceSku
    policy = 'TRIAL_ONLY_NO_PAID_FALLBACK'
    status = 'PASS'
  } | ConvertTo-Json -Depth 5)
)
