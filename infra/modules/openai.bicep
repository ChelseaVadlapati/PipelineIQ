// openai.bicep
// Azure OpenAI account + GPT-4o deployment
//
// NOTE: Azure OpenAI requires approved access. Request it at:
// https://aka.ms/oai/access
// Supported regions for GPT-4o: eastus, eastus2, swedencentral, westus, westus3
// Check current availability before deploying.

@description('Name prefix for all resources')
param prefix string

@description('Azure region — must support GPT-4o')
param location string

@description('Resource tags')
param tags object = {}

@description('GPT-4o deployment name (used in AZURE_OPENAI_DEPLOYMENT app setting)')
param deploymentName string = 'gpt-4o'

@description('Tokens-per-minute capacity (in thousands). 10 = 10K TPM.')
param capacityK int = 10

// ── Account ───────────────────────────────────────────────────────────────────

resource openAiAccount 'Microsoft.CognitiveServices/accounts@2024-04-01-preview' = {
  name: '${prefix}-openai'
  location: location
  tags: tags
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: '${prefix}-openai'
    publicNetworkAccess: 'Enabled'
  }
}

// ── GPT-4o deployment ─────────────────────────────────────────────────────────

resource gpt4oDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-04-01-preview' = {
  parent: openAiAccount
  name: deploymentName
  sku: {
    name: 'Standard'
    capacity: capacityK
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-4o'
      version: '2024-11-20'
    }
    versionUpgradeOption: 'OnceNewDefaultVersionAvailable'
  }
}

// ── Outputs ───────────────────────────────────────────────────────────────────

output accountName string = openAiAccount.name
output endpoint string = openAiAccount.properties.endpoint
output apiKey string = openAiAccount.listKeys().key1
output deploymentName string = gpt4oDeployment.name
