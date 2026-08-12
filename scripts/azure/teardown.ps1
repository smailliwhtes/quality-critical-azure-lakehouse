[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$projectResourceGroup = 'rg-qcal-part4-dev'
$managedResourceGroup = 'rg-qcal-part4-dbx-managed'
$budgetName = 'qcal-part4-budget'
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..')).Path
$receiptPath = Join-Path $repoRoot 'evidence\public\receipts\teardown.json'

if ($projectResourceGroup -ne 'rg-qcal-part4-dev' -or $managedResourceGroup -ne 'rg-qcal-part4-dbx-managed') {
  throw 'Refusing teardown because the exact isolated resource-group names changed.'
}

$started = (Get-Date).ToUniversalTime()
$preInventory = az resource list --resource-group $projectResourceGroup --query '[].{name:name,type:type,location:location}' --output json 2>$null

if ((az group exists --name $projectResourceGroup) -eq 'true') {
  az group delete --name $projectResourceGroup --yes --no-wait
}

$deadline = (Get-Date).ToUniversalTime().AddMinutes(30)
while ((Get-Date).ToUniversalTime() -lt $deadline) {
  $projectExists = (az group exists --name $projectResourceGroup) -eq 'true'
  $managedExists = (az group exists --name $managedResourceGroup) -eq 'true'
  if (-not $projectExists -and -not $managedExists) { break }
  if (-not $projectExists -and $managedExists) {
    az group delete --name $managedResourceGroup --yes --no-wait
  }
  Start-Sleep -Seconds 15
}

$projectAbsent = (az group exists --name $projectResourceGroup) -eq 'false'
$managedAbsent = (az group exists --name $managedResourceGroup) -eq 'false'
if (-not $projectAbsent -or -not $managedAbsent) {
  throw 'Authoritative resource-group readback did not confirm teardown before the deadline.'
}

az consumption budget delete --budget-name $budgetName --output none 2>$null
$budgetReadback = az consumption budget show --budget-name $budgetName --output none 2>$null
$budgetAbsent = $LASTEXITCODE -ne 0
if (-not $budgetAbsent) { throw 'Part 4 budget still exists after teardown.' }

$preCount = 0
if ($preInventory) { $preCount = @($preInventory | ConvertFrom-Json).Count }
$receipt = @{
  schema = 'part4-teardown-receipt/v1'
  started_at_utc = $started.ToString('o')
  completed_at_utc = (Get-Date).ToUniversalTime().ToString('o')
  project_resource_group = $projectResourceGroup
  managed_resource_group = $managedResourceGroup
  pre_teardown_resource_count = $preCount
  project_resource_group_absent = $projectAbsent
  managed_resource_group_absent = $managedAbsent
  part4_budget_absent = $budgetAbsent
  unrelated_resources_targeted = $false
  validation = 'PASS'
  statement = 'The demonstrated Azure environment was intentionally deprovisioned and can be reconstructed from source-controlled infrastructure.'
}
New-Item -ItemType Directory -Path (Split-Path -Parent $receiptPath) -Force | Out-Null
[IO.File]::WriteAllText($receiptPath, ($receipt | ConvertTo-Json -Depth 5))

