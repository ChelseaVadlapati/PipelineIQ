using '../main.bicep'

param environment = 'dev'

// Region — change to one near you that supports GPT-4o
param location = 'eastus2'
param openAiLocation = 'eastus2'

// Cosmos DB — serverless is cheaper for low-traffic dev
param cosmosServerless = true

// Azure DevOps — fill in before deploying
param devOpsOrgUrl = 'https://dev.azure.com/your-org'

// Secrets — pass via --parameters on the CLI or store in a Key Vault reference:
//   az deployment group create ... \
//     --parameters devOpsPat=$AZURE_DEVOPS_PAT webhookSecret=$WEBHOOK_SECRET
param devOpsPat = readEnvironmentVariable('AZURE_DEVOPS_PAT')
param webhookSecret = readEnvironmentVariable('WEBHOOK_SECRET')
