[CmdletBinding()]
param(
  [string]$ResourceGroupName = 'rg-qcal-part4-dev',
  [string]$ExecutionCommit = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ($ResourceGroupName -ne 'rg-qcal-part4-dev') {
  throw 'OIDC validation is fixed to the isolated Part 4 resource group.'
}

$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..')).Path
$receiptRoot = Join-Path $repoRoot 'evidence\public\receipts'
New-Item -ItemType Directory -Path $receiptRoot -Force | Out-Null

if (-not $ExecutionCommit) {
  $ExecutionCommit = if ($env:GITHUB_SHA) { $env:GITHUB_SHA } else { (git -C $repoRoot rev-parse HEAD).Trim() }
}
if ($ExecutionCommit -notmatch '^[0-9a-f]{40}$') {
  throw 'ExecutionCommit must be a full Git commit SHA.'
}

$groupExists = (az group exists --name $ResourceGroupName).Trim()
if ($LASTEXITCODE -ne 0 -or $groupExists -ne 'true') {
  throw 'The isolated Part 4 resource group is not available to the federated identity.'
}

$workspaceSku = (
  az resource list --resource-group $ResourceGroupName `
    --resource-type 'Microsoft.Databricks/workspaces' --query '[0].sku.name' --output tsv
).Trim()
if ($LASTEXITCODE -ne 0 -or $workspaceSku -ne 'trial') {
  throw 'OIDC readback did not reconcile the Databricks workspace to Trial.'
}

$deploymentName = if ($env:GITHUB_RUN_ID) {
  "github-oidc-$($env:GITHUB_RUN_ID)"
} else {
  'github-oidc-local-validation'
}
$template = Join-Path $repoRoot 'infra\oidc-validation.bicep'
az deployment group create --resource-group $ResourceGroupName --name $deploymentName `
  --template-file $template --parameters "executionCommit=$ExecutionCommit" `
  --only-show-errors --output none
if ($LASTEXITCODE -ne 0) { throw 'Resource-group-scoped OIDC deployment failed.' }

$storageAccountName = (
  az storage account list --resource-group $ResourceGroupName --query '[0].name' --output tsv
).Trim()
if ($LASTEXITCODE -ne 0 -or -not $storageAccountName) {
  throw 'Storage discovery failed for the federated identity.'
}
$validationDirectory = "volume/oidc-validation/$ExecutionCommit"
az storage fs directory create --account-name $storageAccountName --file-system evidence `
  --name $validationDirectory --auth-mode login --only-show-errors --output none
if ($LASTEXITCODE -ne 0) { throw 'OIDC managed-identity storage data-plane validation failed.' }

$inventory = az resource list --resource-group $ResourceGroupName `
  --query '[].{type:type}' --output json | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw 'OIDC resource inventory readback failed.' }
$resourceTypes = @($inventory | ForEach-Object { $_.type } | Sort-Object -Unique)
$receipt = [ordered]@{
  schema = 'part4-github-oidc-validation/v1'
  captured_at_utc = (Get-Date).ToUniversalTime().ToString('o')
  execution_commit = $ExecutionCommit
  operation = 'deploy-run-collect'
  deployment_scope = 'RESOURCE_GROUP_ONLY'
  deployment_status = 'SUCCEEDED'
  workspace_sku = $workspaceSku
  storage_authentication = 'FEDERATED_MANAGED_IDENTITY_AZURE_AD'
  storage_data_plane_write = 'SUCCEEDED'
  resource_count = @($inventory).Count
  resource_types = $resourceTypes
  subscription_identifiers_included = $false
  long_lived_secret_used = $false
  validation = 'PASS'
}
[IO.File]::WriteAllText(
  (Join-Path $receiptRoot 'github-oidc-validation.json'),
  ($receipt | ConvertTo-Json -Depth 10)
)
