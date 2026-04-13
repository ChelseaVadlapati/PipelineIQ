// main.bicep
// Orchestrates all PipelineIQ modules.
//
// Deploy:
//   az deployment group create \
//     --resource-group rg-pipelineiq-dev \
//     --template-file infra/main.bicep \
//     --parameters infra/parameters/dev.bicepparam

targetScope = 'resourceGroup'

// ── Parameters ────────────────────────────────────────────────────────────────

@description('Short environment name appended to all resource names (dev | prod)')
@allowed(['dev', 'prod'])
param environment string = 'dev'

@description('Azure region for all resources')
param location string = resourceGroup().location

@description('Azure DevOps organization URL (e.g. https://dev.azure.com/myorg)')
param devOpsOrgUrl string

@description('Azure DevOps PAT with Build (Read) scope')
@secure()
param devOpsPat string

@description('Shared secret validated on incoming webhooks')
@secure()
param webhookSecret string

@description('Azure OpenAI region — must support GPT-4o (e.g. eastus)')
param openAiLocation string = location

@description('Use serverless Cosmos DB capacity (recommended for dev)')
param cosmosServerless bool = (environment == 'dev')

@description('Azure Static Web App SKU (Free for dev, Standard for prod)')
param swaSku string = (environment == 'dev') ? 'Free' : 'Standard'

// ── Locals ────────────────────────────────────────────────────────────────────

var prefix = 'pipelineiq-${environment}'

var tags = {
  project: 'PipelineIQ'
  environment: environment
  managedBy: 'bicep'
}

// ── Modules ───────────────────────────────────────────────────────────────────

module monitoring 'modules/monitoring.bicep' = {
  name: 'monitoring'
  params: {
    prefix: prefix
    location: location
    tags: tags
  }
}

module cosmos 'modules/cosmos.bicep' = {
  name: 'cosmos'
  params: {
    prefix: prefix
    location: location
    tags: tags
    serverless: cosmosServerless
  }
}

module openai 'modules/openai.bicep' = {
  name: 'openai'
  params: {
    prefix: prefix
    location: openAiLocation
    tags: tags
  }
}

module functions 'modules/functions.bicep' = {
  name: 'functions'
  params: {
    prefix: prefix
    location: location
    tags: tags
    appInsightsConnectionString: monitoring.outputs.connectionString
    cosmosEndpoint: cosmos.outputs.endpoint
    cosmosKey: cosmos.outputs.primaryKey
    cosmosConnectionString: cosmos.outputs.connectionString
    openAiEndpoint: openai.outputs.endpoint
    openAiApiKey: openai.outputs.apiKey
    openAiDeployment: openai.outputs.deploymentName
    devOpsOrgUrl: devOpsOrgUrl
    devOpsPat: devOpsPat
    webhookSecret: webhookSecret
  }
}

module frontend 'modules/static-web-app.bicep' = {
  name: 'frontend'
  params: {
    prefix: prefix
    location: location
    tags: tags
    sku: swaSku
  }
}

// ── Outputs ───────────────────────────────────────────────────────────────────

@description('URL for the React dashboard')
output dashboardUrl string = 'https://${frontend.outputs.defaultHostname}'

@description('Azure DevOps webhook URL (use as Service Hook target)')
output webhookUrl string = functions.outputs.webhookUrl

@description('SWA deployment token (used in CI/CD to publish the frontend)')
output swaDeploymentToken string = frontend.outputs.deploymentToken

@description('Function App name (for func azure functionapp publish)')
output functionAppName string = functions.outputs.functionAppName
