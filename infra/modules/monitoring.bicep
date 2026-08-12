param logAnalyticsName string
param location string
param tags object
param dataFactoryName string
param eventHubsNamespaceName string
param keyVaultName string
param storageAccountName string

resource logs 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: logAnalyticsName
  location: location
  tags: tags
  properties: {
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
    retentionInDays: 30
    sku: {
      name: 'PerGB2018'
    }
    workspaceCapping: {
      dailyQuotaGb: 1
    }
  }
}

resource factory 'Microsoft.DataFactory/factories@2018-06-01' existing = {
  name: dataFactoryName
}

resource eventHubs 'Microsoft.EventHub/namespaces@2024-01-01' existing = {
  name: eventHubsNamespaceName
}

resource vault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: keyVaultName
}

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' existing = {
  name: storageAccountName
}

resource factoryDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'send-to-part4-logs'
  scope: factory
  properties: {
    logAnalyticsDestinationType: 'Dedicated'
    workspaceId: logs.id
    logs: [
      {
        categoryGroup: 'allLogs'
        enabled: true
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
      }
    ]
  }
}

resource eventHubsDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'send-to-part4-logs'
  scope: eventHubs
  properties: {
    logAnalyticsDestinationType: 'Dedicated'
    workspaceId: logs.id
    logs: [
      {
        categoryGroup: 'allLogs'
        enabled: true
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
      }
    ]
  }
}

resource vaultDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'send-to-part4-logs'
  scope: vault
  properties: {
    logAnalyticsDestinationType: 'Dedicated'
    workspaceId: logs.id
    logs: [
      {
        categoryGroup: 'allLogs'
        enabled: true
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
      }
    ]
  }
}

resource storageDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'send-to-part4-logs'
  scope: storage
  properties: {
    logAnalyticsDestinationType: 'Dedicated'
    workspaceId: logs.id
    metrics: [
      {
        category: 'Transaction'
        enabled: true
      }
    ]
  }
}

resource failedAdminAlert 'Microsoft.Insights/activityLogAlerts@2020-10-01' = {
  name: 'part4-failed-administrative-operation'
  location: 'global'
  tags: tags
  properties: {
    actions: {
      actionGroups: []
    }
    condition: {
      allOf: [
        {
          equals: 'Administrative'
          field: 'category'
        }
        {
          equals: 'Failed'
          field: 'status'
        }
      ]
    }
    description: 'Detects failed Azure control-plane operations in the isolated Part 4 resource group.'
    enabled: true
    scopes: [
      resourceGroup().id
    ]
  }
}

output logAnalyticsWorkspaceId string = logs.id
output logAnalyticsWorkspaceName string = logs.name
output alertRuleName string = failedAdminAlert.name
