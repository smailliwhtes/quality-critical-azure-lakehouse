targetScope = 'subscription'

@description('Azure region verified for the bounded Part 4 deployment.')
@allowed([
  'eastus2'
])
param location string = 'eastus2'

param resourceGroupName string = 'rg-qcal-part4-dev'
param managedResourceGroupName string = 'rg-qcal-part4-dbx-managed'
param projectName string = 'qcal-part4'

@description('Fail-closed cloud budget. Deployment automation supplies PART4_BUDGET_USD.')
@minValue(1)
param PART4_BUDGET_USD int = 20

@secure()
@description('Optional deployment principal object ID for temporary Key Vault secret administration.')
param deployerObjectId string = ''

@secure()
@description('Optional Microsoft Azure Databricks application object ID for a Key Vault-backed secret scope.')
param databricksServicePrincipalObjectId string = ''

@description('Start of the twelve-month budget window.')
param budgetStartDate string = utcNow('yyyy-MM-01')

var suffix = uniqueString(subscription().id, projectName)
var tags = {
  project: 'linkedin-part4'
  purpose: 'portfolio'
  managedBy: 'bicep'
  environment: 'demo'
}

module budgetModule './modules/budget.bicep' = {
  name: 'budget-${uniqueString(resourceGroupName)}'
  params: {
    budgetAmount: PART4_BUDGET_USD
    budgetName: '${projectName}-budget'
    budgetStartDate: budgetStartDate
    resourceGroupName: resourceGroupName
  }
}

resource projectResourceGroup 'Microsoft.Resources/resourceGroups@2024-11-01' = {
  name: resourceGroupName
  location: location
  tags: tags
  dependsOn: [
    budgetModule
  ]
}

module identities './modules/identities.bicep' = {
  name: 'identities-${suffix}'
  scope: projectResourceGroup
  params: {
    location: location
    identityName: 'id-${projectName}-github'
    tags: tags
  }
}

module storage './modules/storage.bicep' = {
  name: 'storage-${suffix}'
  scope: projectResourceGroup
  params: {
    location: location
    storageAccountName: take('stqcal${suffix}', 24)
    tags: tags
  }
}

module dataFactory './modules/data-factory.bicep' = {
  name: 'adf-${suffix}'
  scope: projectResourceGroup
  params: {
    factoryName: 'adf-${projectName}-${suffix}'
    location: location
    tags: tags
  }
}

module eventHubs './modules/event-hubs.bicep' = {
  name: 'eventhubs-${suffix}'
  scope: projectResourceGroup
  params: {
    eventHubName: 'quality-telemetry'
    location: location
    namespaceName: 'evh-${projectName}-${suffix}'
    tags: tags
  }
}

module keyVault './modules/key-vault.bicep' = {
  name: 'keyvault-${suffix}'
  scope: projectResourceGroup
  params: {
    databricksServicePrincipalObjectId: databricksServicePrincipalObjectId
    deployerObjectId: deployerObjectId
    location: location
    tags: tags
    vaultName: take('kv-${projectName}-${suffix}', 24)
  }
}

module accessConnector './modules/access-connector.bicep' = {
  name: 'access-connector-${suffix}'
  scope: projectResourceGroup
  params: {
    connectorName: 'ac-${projectName}-${suffix}'
    location: location
    tags: tags
  }
}

module databricks './modules/databricks.bicep' = {
  name: 'databricks-${suffix}'
  scope: projectResourceGroup
  params: {
    location: location
    managedResourceGroupName: managedResourceGroupName
    tags: tags
    workspaceName: 'dbw-${projectName}-${suffix}'
  }
}

module rbac './modules/rbac.bicep' = {
  name: 'rbac-${suffix}'
  scope: projectResourceGroup
  params: {
    accessConnectorPrincipalId: accessConnector.outputs.principalId
    dataFactoryPrincipalId: dataFactory.outputs.principalId
    deployerPrincipalId: deployerObjectId
    githubIdentityPrincipalId: identities.outputs.githubIdentityPrincipalId
  }
}

module monitoring './modules/monitoring.bicep' = {
  name: 'monitoring-${suffix}'
  scope: projectResourceGroup
  params: {
    dataFactoryName: dataFactory.outputs.factoryName
    databricksWorkspaceName: databricks.outputs.workspaceName
    eventHubsNamespaceName: eventHubs.outputs.namespaceName
    keyVaultName: keyVault.outputs.vaultName
    location: location
    logAnalyticsName: 'log-${projectName}-${suffix}'
    storageAccountName: storage.outputs.storageAccountName
    tags: tags
  }
}

output resourceGroupName string = projectResourceGroup.name
output storageAccountName string = storage.outputs.storageAccountName
output dataFactoryName string = dataFactory.outputs.factoryName
output eventHubsNamespaceName string = eventHubs.outputs.namespaceName
output eventHubName string = eventHubs.outputs.eventHubName
output keyVaultName string = keyVault.outputs.vaultName
output accessConnectorId string = accessConnector.outputs.connectorId
output databricksWorkspaceName string = databricks.outputs.workspaceName
output logAnalyticsWorkspaceName string = monitoring.outputs.logAnalyticsWorkspaceName
output githubIdentityClientId string = identities.outputs.githubIdentityClientId
output trialPolicy string = 'TRIAL_ONLY_NO_PAID_FALLBACK'
