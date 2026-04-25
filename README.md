# AzL-Pools

Pool prospecting lead-generation platform running on Arc-enabled AKS (Azure Local) with Foundry Local for CPU-based AI inference.

## What It Does

1. **Identifies** Florida homes valued ≥$1M that lack swimming pools (ATTOM API + aerial imagery ML)
2. **Designs** parametric pool concepts using on-prem AI (Foundry Local / Phi-4-mini on CPU)
3. **Enriches** homeowner contact details from public records
4. **Manages** outreach campaigns via a web dashboard

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│               Azure Local (Azure Stack HCI)                  │
│             Arc-enabled AKS + Flux GitOps                    │
│                                                              │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────────┐  │
│  │ Data Ingest  │  │ Pool Detect   │  │ Pool Design      │  │
│  │ (FastAPI)    │  │ (U-Net/ONNX)  │  │ (Foundry Local)  │  │
│  └──────┬───────┘  └──────┬────────┘  └──────┬───────────┘  │
│         │                 │                   │              │
│         ▼                 ▼                   ▼              │
│  ┌──────────┐     ┌────────────┐     ┌──────────────────┐   │
│  │ Postgres │     │ Redis Queue│     │ Contact Enrich   │   │
│  │ (PostGIS)│     │ (ARQ)      │     │ (Melissa/TLOxp)  │   │
│  └──────────┘     └────────────┘     └──────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Dashboard (React + FastAPI)                           │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

## Repo Structure

```
├── clusters/          # Flux entry points per environment
├── infrastructure/    # Cluster-wide infra (KEDA, ingress, monitoring)
├── apps/              # Kustomize base+overlays per service
├── src/               # Application source code
├── image-automation/  # Flux image update automation
├── db/                # Database migrations
├── docs/              # Architecture, runbooks, compliance
└── .github/workflows/ # CI/CD pipelines
```

## GitOps (Flux v2)

This repo is the single source of truth. Flux watches `main` and reconciles:

```bash
# Bootstrap on Arc-enabled cluster
az k8s-configuration flux create \
  --resource-group azl-pools-rg \
  --cluster-name azl-pools-cluster \
  --cluster-type connectedClusters \
  --name azl-pools-gitops \
  --namespace flux-system \
  --scope cluster \
  --url https://github.com/mgodfre3/AzL-Pools \
  --branch main \
  --kustomization name=infra path=./clusters/prod
```

## Quick Start (Local Dev)

```bash
docker compose up -d          # Postgres + Redis + services
cd src/data-ingestion && pip install -r requirements.txt
uvicorn main:app --reload     # http://localhost:8000
```

## License

MIT
