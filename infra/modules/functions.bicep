// functions.bicep
// Storage account + Consumption plan + Python Function App

@description('Name prefix for all resources')
param prefix string

@description('Azure region')
param location string

@description('Resource tags')
param tags object = {}

// ── Wired-in outputs from other modules ───────────────────────────────────────

@description('Application Insights connection string')
param appInsightsConnectionString string

@description('Cosmos DB endpoint')
param cosmosEndpoint string

@description('Cosmos DB primary key')
@secure()
param cosmosKey string

@description('Cosmos DB full connection string (for change-feed trigger)')
@secure()
param cosmosConnectionString string

@description('Azure OpenAI endpoint')
param openAiEndpoint string

@description('Azure OpenAI API key')
@secure()
param openAiApiKey string

@description('Azure OpenAI deployment name')
param openAiDeployment string

@description('Azure DevOps organization URL')
param devOpsOrgUrl string

@description('Azure DevOps Personal Access Token')
@secure()
param devOpsPat string

@description('Webhook shared secret')
@secure()
param webhookSecret string

// ── Storage account (required by Functions runtime) ───────────────────────────

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: '${replace(prefix, '-', '')}store'  // storage names: alphanumeric only, max 24 chars
  location: location
  tags: tags
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    supportsHttpsTrafficOnly: true
  }
}

var storageConnectionString = 'DefaultEndpointsProtocol=https;AccountName=${storage.name};EndpointSuffix=${environment().suffixes.storage};AccountKey=${storage.listKeys().keys[0].value}'

// ── Consumption plan ──────────────────────────────────────────────────────────

resource plan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: '${prefix}-plan'
  location: location
  tags: tags
  sku: {
    name: 'Y1'
    tier: 'Dynamic'
  }
  properties: {
    reserved: true  // required for Linux
  }
}

// ── Function App ──────────────────────────────────────────────────────────────

resource functionApp 'Microsoft.Web/sites@2023-12-01' = {
  name: '${prefix}-functions'
  location: location
  tags: tags
  kind: 'functionapp,linux'
  properties: {
    serverFarmId: plan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'Python|3.11'
      pythonVersion: '3.11'
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      cors: {
        allowedOrigins: ['*']
        supportCredentials: false
      }
      appSettings: [
        // ── Functions runtime ──────────────────────────────────────────────
        { name: 'AzureWebJobsStorage', value: storageConnectionString }
        { name: 'FUNCTIONS_EXTENSION_VERSION', value: '~4' }
        { name: 'FUNCTIONS_WORKER_RUNTIME', value: 'python' }
        { name: 'WEBSITE_RUN_FROM_PACKAGE', value: '1' }

        // ── Monitoring ─────────────────────────────────────────────────────
        { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: appInsightsConnectionString }

        // ── Cosmos DB ──────────────────────────────────────────────────────
        { name: 'COSMOS_ENDPOINT', value: cosmosEndpoint }
        { name: 'COSMOS_KEY', value: cosmosKey }
        { name: 'COSMOS_DB', value: 'pipelineiq' }
        { name: 'COSMOS_CONTAINER', value: 'analyses' }
        { name: 'CosmosDbConnectionString', value: cosmosConnectionString }

        // ── Azure OpenAI ───────────────────────────────────────────────────
        { name: 'AZURE_OPENAI_ENDPOINT', value: openAiEndpoint }
        { name: 'AZURE_OPENAI_API_KEY', value: openAiApiKey }
        { name: 'AZURE_OPENAI_DEPLOYMENT', value: openAiDeployment }

        // ── Azure DevOps ───────────────────────────────────────────────────
        { name: 'AZURE_DEVOPS_ORG_URL', value: devOpsOrgUrl }
        { name: 'AZURE_DEVOPS_PAT', value: devOpsPat }

        // ── Webhook ────────────────────────────────────────────────────────
        { name: 'WEBHOOK_SECRET', value: webhookSecret }
      ]
    }
  }
}

// ── Outputs ───────────────────────────────────────────────────────────────────

output functionAppName string = functionApp.name
output functionAppHostname string = functionApp.properties.defaultHostName
output webhookUrl string = 'https://${functionApp.properties.defaultHostName}/api/webhook'
