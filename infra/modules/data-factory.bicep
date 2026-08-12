param factoryName string
param location string
param tags object

resource factory 'Microsoft.DataFactory/factories@2018-06-01' = {
  name: factoryName
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    publicNetworkAccess: 'Enabled'
  }
}

output factoryId string = factory.id
output factoryName string = factory.name
output principalId string = factory.identity.principalId

