param githubIdentityPrincipalId string
param accessConnectorPrincipalId string
param dataFactoryPrincipalId string
param deployerPrincipalId string = ''

var ownerRoleDefinitionId = subscriptionResourceId(
  'Microsoft.Authorization/roleDefinitions',
  '8e3af657-a8ff-443c-a75c-2fe8c4bcb635'
)
var storageBlobDataContributorRoleDefinitionId = subscriptionResourceId(
  'Microsoft.Authorization/roleDefinitions',
  'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
)

resource githubOwnerRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, githubIdentityPrincipalId, ownerRoleDefinitionId)
  properties: {
    principalId: githubIdentityPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: ownerRoleDefinitionId
  }
}

resource accessConnectorStorageRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, accessConnectorPrincipalId, storageBlobDataContributorRoleDefinitionId)
  properties: {
    principalId: accessConnectorPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: storageBlobDataContributorRoleDefinitionId
  }
}

resource dataFactoryStorageRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, dataFactoryPrincipalId, storageBlobDataContributorRoleDefinitionId)
  properties: {
    principalId: dataFactoryPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: storageBlobDataContributorRoleDefinitionId
  }
}

resource githubStorageRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, githubIdentityPrincipalId, storageBlobDataContributorRoleDefinitionId)
  properties: {
    principalId: githubIdentityPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: storageBlobDataContributorRoleDefinitionId
  }
}

resource deployerStorageRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(deployerPrincipalId)) {
  name: guid(resourceGroup().id, deployerPrincipalId, storageBlobDataContributorRoleDefinitionId)
  properties: {
    principalId: deployerPrincipalId
    principalType: 'User'
    roleDefinitionId: storageBlobDataContributorRoleDefinitionId
  }
}

output roleAssignmentNames array = [
  githubOwnerRole.name
  accessConnectorStorageRole.name
  dataFactoryStorageRole.name
  githubStorageRole.name
]
