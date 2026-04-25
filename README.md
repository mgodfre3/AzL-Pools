# AzL-Pools

Pool prospecting lead-generation platform built on **Azure Functions** with **Durable Functions** orchestration, packaged for the **Azure Marketplace**.

## What It Does

1. **Identifies** Florida homes valued ≥$1M that lack swimming pools (ATTOM API + aerial imagery ML)
2. **Designs** parametric pool concepts using Azure OpenAI / Foundry Local (CPU)
3. **Enriches** homeowner contact details from public records
4. **Manages** outreach campaigns via a web dashboard

## Architecture

```
                        ┌─────────────────────────────┐
                        │     Azure Functions App      │
                        │   (Consumption / Premium)    │
                        │                              │
  HTTP ────────────────▶│  api/        REST endpoints  │
                        │  orchestrator/ Durable Fns   │
  Timer ───────────────▶│  data_ingestion/  ATTOM sync │
  Queue ───────────────▶│  pool_detection/  U-Net ONNX │
  Queue ───────────────▶│  pool_design/   AI design    │
  Queue ───────────────▶│  contact_enrichment/ enrich  │
                        └──────────┬───────────────────┘
                                   │
            ┌──────────────────────┼──────────────────────┐
            ▼                      ▼                      ▼
  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
  │ Azure PostgreSQL │  │ Azure Storage    │  │ Azure OpenAI /   │
  │ Flexible Server  │  │ (Queues + Blobs) │  │ Foundry Local    │
  └──────────────────┘  └──────────────────┘  └──────────────────┘
```

## Marketplace Offering

This solution is packaged as an **Azure Managed Application** for the Azure Marketplace:

```
marketplace/
├── arm/
│   └── mainTemplate.json    # ARM template deploying all resources
├── ui/
│   └── createUiDefinition.json  # Portal wizard for deployment
└── manifest.json
```

Customers deploy via "Get It Now" in the Marketplace → portal wizard collects
API keys and preferences → ARM template provisions all Azure resources.

## Repo Structure

```
├── functions/           # Azure Functions application (Python v2)
│   ├── function_app.py  # Main entry point (all function registrations)
│   ├── orchestrator/    # Durable Functions orchestrators
│   ├── data_ingestion/  # ATTOM API + county property data
│   ├── pool_detection/  # U-Net ONNX aerial imagery analysis
│   ├── pool_design/     # AI pool design generation
│   ├── contact_enrichment/ # Melissa skip-trace enrichment
│   ├── api/             # HTTP API endpoints (dashboard backend)
│   └── shared/          # Shared models, DB, utilities
├── infra/               # Bicep IaC for Azure resources
├── marketplace/         # Azure Marketplace packaging (ARM + UI)
├── src/dashboard/       # React frontend (Static Web App)
├── db/                  # Database migrations
├── docs/                # Architecture, compliance, runbooks
└── .github/workflows/   # CI/CD
```

## Quick Start (Local Dev)

```bash
# Prerequisites: Azure Functions Core Tools, Python 3.12, Node 20
cd functions
pip install -r requirements.txt
func start                    # http://localhost:7071

# Frontend
cd src/dashboard/frontend
npm install && npm run dev    # http://localhost:5173
```

## Deploy to Azure

```bash
# Deploy infrastructure
az deployment group create -g azl-pools-rg -f infra/main.bicep

# Deploy functions
cd functions && func azure functionapp publish azl-pools-func

# Deploy frontend
cd src/dashboard/frontend && npm run build
az staticwebapp upload --app-name azl-pools-web
```

## License

MIT
