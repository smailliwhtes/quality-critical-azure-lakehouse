param vaultName string
param location string
param tags object
@secure()
param deployerObjectId string = ''
@secure()
param databricksServicePrincipalObjectId string = ''

var deployerAccessPolicy = empty(deployerObjectId) ? [] : [
  {
    objectId: deployerObjectId
    permissions: {
      certificates: []
      keys: []
      secrets: [
        'get'
        'list'
        'set'
        'delete'
      ]
      storage: []
    }
    tenantId: subscription().tenantId
  }
]
var databricksAccessPolicy = empty(databricksServicePrincipalObjectId) ? [] : [
  {
    objectId: databricksServicePrincipalObjectId
    permissions: {
      certificates: []
      keys: []
      secrets: [
        'get'
        'list'
      ]
      storage: []
    }
    tenantId: subscription().tenantId
  }
]

resource vault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: vaultName
  location: location
  tags: tags
  properties: {
    accessPolicies: concat(deployerAccessPolicy, databricksAccessPolicy)
    enableRbacAuthorization: false
    enableSoftDelete: true
    publicNetworkAccess: 'Enabled'
    sku: {
      family: 'A'
      name: 'standard'
    }
    softDeleteRetentionInDays: 7
    tenantId: subscription().tenantId
  }
}

output vaultId string = vault.id
output vaultName string = vault.name
output vaultUri string = vault.properties.vaultUri
