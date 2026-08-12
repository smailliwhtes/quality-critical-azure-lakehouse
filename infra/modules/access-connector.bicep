param connectorName string
param location string
param tags object

resource connector 'Microsoft.Databricks/accessConnectors@2023-05-01' = {
  name: connectorName
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {}
}

output connectorId string = connector.id
output connectorName string = connector.name
output principalId string = connector.identity.principalId

