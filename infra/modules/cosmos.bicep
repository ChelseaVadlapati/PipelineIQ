// cosmos.bicep
// Cosmos DB account, pipelineiq database, and required containers

@description('Name prefix for all resources')
param prefix string

@description('Azure region')
param location string

@description('Resource tags')
param tags object = {}

@description('Use serverless capacity (good for dev/low-traffic). Set false for provisioned throughput in prod.')
param serverless bool = true

// ── Account ───────────────────────────────────────────────────────────────────

resource account 'Microsoft.DocumentDB/databaseAccounts@2024-02-15-preview' = {
  name: '${prefix}-cosmos'
  location: location
  tags: tags
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    capabilities: serverless ? [{ name: 'EnableServerless' }] : []
    enableFreeTier: false
    backupPolicy: {
      type: 'Periodic'
      periodicModeProperties: {
        backupIntervalInMinutes: 240
        backupRetentionIntervalInHours: 8
        backupStorageRedundancy: 'Local'
      }
    }
  }
}

// ── Database ──────────────────────────────────────────────────────────────────

resource database 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2024-02-15-preview' = {
  parent: account
  name: 'pipelineiq'
  properties: {
    resource: {
      id: 'pipelineiq'
    }
  }
}

// ── Containers ────────────────────────────────────────────────────────────────

// Pipeline run documents (written by webhook_receiver)
resource runsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-02-15-preview' = {
  parent: database
  name: 'runs'
  properties: {
    resource: {
      id: 'runs'
      partitionKey: {
        paths: ['/id']
        kind: 'Hash'
      }
      defaultTtl: 2592000 // 30 days — raw run docs don't need to live forever
      indexingPolicy: {
        indexingMode: 'consistent'
        includedPaths: [{ path: '/*' }]
        excludedPaths: [{ path: '/"_etag"/?' }]
      }
    }
  }
}

// AI analysis documents (written by pipeline_analyzer)
resource analysesContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-02-15-preview' = {
  parent: database
  name: 'analyses'
  properties: {
    resource: {
      id: 'analyses'
      partitionKey: {
        paths: ['/id']
        kind: 'Hash'
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        includedPaths: [{ path: '/*' }]
        excludedPaths: [{ path: '/"_etag"/?' }]
        compositeIndexes: [
          [
            { path: '/analyzed_at', order: 'descending' }
            { path: '/id', order: 'ascending' }
          ]
        ]
      }
    }
  }
}

// Leases container — required by the Cosmos DB change-feed trigger
resource leasesContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-02-15-preview' = {
  parent: database
  name: 'leases'
  properties: {
    resource: {
      id: 'leases'
      partitionKey: {
        paths: ['/id']
        kind: 'Hash'
      }
    }
  }
}

// ── Outputs ───────────────────────────────────────────────────────────────────

output accountName string = account.name
output endpoint string = account.properties.documentEndpoint
output connectionString string = account.listConnectionStrings().connectionStrings[0].connectionString
output primaryKey string = account.listKeys().primaryMasterKey
