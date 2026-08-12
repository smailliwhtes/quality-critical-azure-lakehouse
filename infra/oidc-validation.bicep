targetScope = 'resourceGroup'

@minLength(40)
@maxLength(40)
param executionCommit string

output schema string = 'part4-github-oidc-deployment/v1'
output validation string = 'RESOURCE_GROUP_SCOPED_DEPLOYMENT_SUCCEEDED'
output executionCommit string = executionCommit
