using '../main.bicep'

param environment = 'prod'

param location = 'eastus'
param openAiLocation = 'eastus'

// Provisioned throughput in prod (set cosmosServerless = false)
param cosmosServerless = false

// Standard SWA tier for custom domains + auth
param swaSku = 'Standard'

param devOpsOrgUrl = 'https://dev.azure.com/your-org'

// Secrets — always inject at deploy time, never commit values here
param devOpsPat = readEnvironmentVariable('AZURE_DEVOPS_PAT')
param webhookSecret = readEnvironmentVariable('WEBHOOK_SECRET')
