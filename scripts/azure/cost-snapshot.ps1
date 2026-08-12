[CmdletBinding()]
param(
  [ValidateSet('start', 'infrastructure', 'ingestion', 'incident-performance', 'pre-teardown', 'final')]
  [string]$Stage = 'start',
  [string]$ResourceGroupName = 'rg-qcal-part4-dev',
  [string]$OutputPath = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ($ResourceGroupName -ne 'rg-qcal-part4-dev') {
  throw 'Cost capture is fixed to the isolated Part 4 resource group.'
}

$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..')).Path
if (-not $OutputPath) {
  $OutputPath = Join-Path $repoRoot "evidence\public\receipts\cost-$Stage.json"
}

$subscriptionId = (az account show --query id --output tsv).Trim()
if ($LASTEXITCODE -ne 0 -or -not $subscriptionId) {
  throw 'An authenticated Azure subscription is required for cost capture.'
}

$body = @{
  type = 'ActualCost'
  timeframe = 'MonthToDate'
  dataset = @{
    granularity = 'None'
    aggregation = @{
      totalCost = @{
        name = 'Cost'
        function = 'Sum'
      }
    }
    filter = @{
      dimensions = @{
        name = 'ResourceGroupName'
        operator = 'In'
        values = @($ResourceGroupName)
      }
    }
  }
} | ConvertTo-Json -Depth 10 -Compress

$url = "https://management.azure.com/subscriptions/$subscriptionId/providers/Microsoft.CostManagement/query?api-version=2025-03-01"
$raw = az rest --method post --url $url --body $body --output json 2>$null
$querySucceeded = $LASTEXITCODE -eq 0
$capturedAt = (Get-Date).ToUniversalTime().ToString('o')

$receipt = [ordered]@{
  schema = 'part4-cost-snapshot/v1'
  captured_at_utc = $capturedAt
  stage = $Stage
  scope = 'rg-qcal-part4-dev-filtered'
  label = 'PENDING BILLING SETTLEMENT'
  amount = $null
  currency = 'USD'
  billing_latency_note = 'Azure cost data can lag actual resource usage.'
  source = 'Azure Cost Management Query API 2025-03-01'
  query_status = if ($querySucceeded) { 'AVAILABLE' } else { 'API_UNAVAILABLE' }
  identifiers_included = $false
}

if ($querySucceeded -and $raw) {
  $response = $raw | ConvertFrom-Json
  $columns = @($response.properties.columns | ForEach-Object { $_.name })
  $rows = @($response.properties.rows)
  $costIndex = [Array]::IndexOf($columns, 'Cost')
  $currencyIndex = [Array]::IndexOf($columns, 'Currency')
  $firstRow = if ($rows.Count -gt 0) { @($rows[0]) } else { @() }
  $amount = if ($firstRow.Count -gt 0 -and $costIndex -ge 0) {
    [decimal]$firstRow[$costIndex]
  } else {
    [decimal]0
  }
  $currency = if ($firstRow.Count -gt 0 -and $currencyIndex -ge 0) {
    [string]$firstRow[$currencyIndex]
  } else {
    'USD'
  }
  $receipt.label = 'CURRENT COST SNAPSHOT'
  $receipt.amount = [math]::Round($amount, 6)
  $receipt.currency = $currency
}

New-Item -ItemType Directory -Path (Split-Path -Parent $OutputPath) -Force | Out-Null
[IO.File]::WriteAllText($OutputPath, ($receipt | ConvertTo-Json -Depth 8))
$receipt | ConvertTo-Json -Depth 8
