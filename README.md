# PipelineIQ

AI-powered pipeline intelligence for Azure DevOps. PipelineIQ receives webhook events from your pipelines, uses GPT-4o to analyze failures, and surfaces root causes and actionable recommendations in a clean dashboard.

---

## How it works

```
Azure DevOps ──webhook──▶ webhook_receiver (Azure Function)
                                │
                                ▼
                         Cosmos DB (runs)
                                │
                  Cosmos change-feed trigger
                                │
                                ▼
                      pipeline_analyzer
                      ├── fetch logs (Azure DevOps API)
                      ├── fetch timeline (failed steps)
                      └── GPT-4o analysis
                                │
                                ▼
                         Cosmos DB (analyses)
                                │
                    api_get_analyses / api_get_analysis
                                │
                                ▼
                         React Dashboard
```

## Project structure

```
PipelineIQ/
├── backend/                   # Azure Functions (Python)
│   ├── shared/
│   │   ├── models.py          # Pydantic data models
│   │   ├── cosmos_client.py   # Cosmos DB helpers
│   │   ├── devops_client.py   # Azure DevOps API client
│   │   └── ai_analyzer.py     # GPT-4o analysis logic
│   ├── webhook_receiver/      # POST /api/webhook
│   ├── pipeline_analyzer/     # Cosmos DB change-feed trigger
│   ├── api_get_analysis/      # GET /api/analyses/{id}
│   ├── api_get_analyses/      # GET /api/analyses
│   ├── host.json
│   └── requirements.txt
├── frontend/                  # React + Vite + Tailwind
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/api.ts
│   │   └── types/index.ts
│   └── package.json
└── infra/                     # Infrastructure as code (Terraform/Bicep)
```

## Prerequisites

- Python 3.11+
- Node.js 20+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/en-us/azure/azure-functions/functions-run-local)
- [Azurite](https://learn.microsoft.com/en-us/azure/storage/common/storage-use-azurite) (local storage emulator)
- An Azure DevOps organization with a PAT scoped to **Build (Read)**
- An Azure OpenAI resource with a `gpt-4o` deployment
- An Azure Cosmos DB account (or use the emulator locally)

## Local development

### Backend

```bash
cd backend
cp local.settings.json.example local.settings.json
# Fill in your values in local.settings.json

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

func start
```

The functions will be available at `http://localhost:7071/api/`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The dashboard runs at `http://localhost:3000`. API calls are proxied to the Functions host.

## Azure DevOps webhook setup

1. In your Azure DevOps project, go to **Project Settings → Service Hooks**.
2. Create a new subscription for **Webhooks**.
3. Select trigger: **Build completed**.
4. Set the URL to your deployed function URL:
   `https://<your-app>.azurewebsites.net/api/webhook?code=<function-key>`
5. Add a custom header `X-Pipeline-Secret: <your-webhook-secret>` matching `WEBHOOK_SECRET` in settings.

## Environment variables

| Variable | Description |
|---|---|
| `AZURE_DEVOPS_ORG_URL` | Your org URL, e.g. `https://dev.azure.com/myorg` |
| `AZURE_DEVOPS_PAT` | Personal access token with Build (Read) scope |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI resource endpoint |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key |
| `AZURE_OPENAI_DEPLOYMENT` | Deployment name (default: `gpt-4o`) |
| `COSMOS_ENDPOINT` | Cosmos DB account endpoint |
| `COSMOS_KEY` | Cosmos DB account key |
| `COSMOS_DB` | Database name (default: `pipelineiq`) |
| `COSMOS_CONTAINER` | Analyses container name (default: `analyses`) |
| `CosmosDbConnectionString` | Full connection string for the change-feed trigger |
| `WEBHOOK_SECRET` | Shared secret validated on incoming webhooks |

## Deploy to Azure (Bicep)

All Azure resources are defined in `infra/` using Bicep.

```bash
# 1. Create a resource group
az group create --name rg-pipelineiq-dev --location eastus

# 2. Export secrets as env vars (never commit these)
export AZURE_DEVOPS_PAT=your-pat
export WEBHOOK_SECRET=your-secret

# 3. Deploy (takes ~3 minutes)
az deployment group create \
  --resource-group rg-pipelineiq-dev \
  --template-file infra/main.bicep \
  --parameters infra/parameters/dev.bicepparam

# 4. Deploy the backend code
cd backend
func azure functionapp publish $(az deployment group show \
  -g rg-pipelineiq-dev -n main \
  --query properties.outputs.functionAppName.value -o tsv)

# 5. Deploy the frontend
cd frontend && npm run build
npx @azure/static-web-apps-cli deploy dist \
  --deployment-token $(az deployment group show \
    -g rg-pipelineiq-dev -n main \
    --query properties.outputs.swaDeploymentToken.value -o tsv)
```

The deployment outputs the **webhook URL** to register in Azure DevOps and the **dashboard URL**.

> **Note:** Azure OpenAI requires approved access. Request it at https://aka.ms/oai/access before deploying. GPT-4o is available in `eastus`, `eastus2`, `swedencentral`, `westus`, and `westus3`.

## Cosmos DB containers

The Bicep deployment creates all containers automatically. When running **locally**, create these manually:

| Container | Partition key |
|---|---|
| `runs` | `/id` |
| `analyses` | `/id` |
| `leases` | `/id` (auto-created by change-feed trigger) |

## API reference

### `GET /api/analyses`

Returns paginated analyses with aggregate stats.

Query params: `limit`, `offset`, `project`, `pipeline`, `result`, `severity`

### `GET /api/analyses/{id}`

Returns a single analysis document.

### `POST /api/webhook`

Receives Azure DevOps `build.complete` events. Requires header `X-Pipeline-Secret`.
