// static-web-app.bicep
// Azure Static Web Apps — hosts the React frontend

@description('Name prefix for all resources')
param prefix string

@description('Azure region')
param location string

@description('Resource tags')
param tags object = {}

@description('SKU: Free (dev) or Standard (prod — required for custom domains + auth)')
@allowed(['Free', 'Standard'])
param sku string = 'Free'

// ── Static Web App ────────────────────────────────────────────────────────────

resource swa 'Microsoft.Web/staticSites@2023-12-01' = {
  name: '${prefix}-frontend'
  location: location
  tags: tags
  sku: {
    name: sku
    tier: sku
  }
  properties: {
    stagingEnvironmentPolicy: 'Enabled'
    allowConfigFileUpdates: true
    enterpriseGradeCdnStatus: 'Disabled'
  }
}

// ── Outputs ───────────────────────────────────────────────────────────────────

output swaName string = swa.name
output defaultHostname string = swa.properties.defaultHostname
output deploymentToken string = swa.listSecrets().properties.apiKey
