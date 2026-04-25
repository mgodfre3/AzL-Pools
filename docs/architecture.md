# AzL Pools — Architecture

## System Overview

See the main [README](../README.md) for the architecture diagram.

## Service Map

| Service | Port | Purpose |
|---------|------|---------|
| data-ingestion | 8000 | ATTOM API + county scraper, property data pipeline |
| pool-detection | 8001 | Aerial imagery fetch + U-Net ONNX pool detection |
| pool-design | 8002 | AI pool design generation via Foundry Local |
| contact-enrichment | 8003 | Melissa/TLOxp skip-trace enrichment |
| dashboard | 8080 | React frontend + FastAPI backend |
| foundry-local | 5273 | Phi-4-mini LLM (CPU, OpenAI-compat API) |
| postgres | 5432 | PostGIS database |
| redis | 6379 | ARQ task queue broker + cache |

## Flux GitOps Flow

```
Git push → Flux Source Controller (1m poll)
  → Kustomization: infrastructure (KEDA, ingress, monitoring)
    → Kustomization: apps (depends on infra)
      → Each app deployed from overlays/{dev,prod}

Image push → Flux Image Automation (1m scan)
  → ImagePolicy selects highest semver tag
  → ImageUpdateAutomation commits tag update to apps/
  → Flux reconciles the new image
```

## Scaling

- **KEDA ScaledObjects** on pool-detection and pool-design scale 1→8 replicas
  based on Redis queue depth (listLength trigger)
- **Foundry Local** is CPU-bound; scale by adding replicas (each needs ~16 GB RAM)
- **Multi-region**: Add a new `clusters/<region>/` directory with region-specific
  overlays (county FIPS codes, API keys)
