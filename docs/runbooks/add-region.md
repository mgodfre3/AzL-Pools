# Adding a New Region — Expansion Runbook

## Overview

To expand AzL Pools to a new state or region, you need to:

1. Add county FIPS codes to the data ingestion configuration
2. Create a cluster overlay (if deploying a separate cluster)
3. Adjust pool design prompts for regional climate/codes

## Step 1: Add County Data to Ingestion

Edit `src/data-ingestion/main.py` and add FIPS codes to the `FLORIDA_COUNTIES` dict
(rename to `TARGET_COUNTIES` when going multi-state):

```python
TARGET_COUNTIES = {
    # Florida
    "12086": "Miami-Dade",
    "12011": "Broward",
    # ... existing FL counties

    # Texas
    "48201": "Harris",      # Houston
    "48113": "Dallas",
    "48453": "Travis",      # Austin

    # Arizona
    "04013": "Maricopa",    # Phoenix/Scottsdale
    "04019": "Pima",        # Tucson
}
```

## Step 2: Create Regional Cluster Overlay (Optional)

If deploying a separate cluster for the new region:

```
clusters/
  prod/          # Florida (existing)
  prod-west/     # Texas + Arizona (new)
    infrastructure.yaml
    apps.yaml
```

The `apps.yaml` Kustomizations point to the same `apps/*/overlays/prod` bases,
but you can create region-specific overlays if needed:

```
apps/data-ingestion/overlays/prod-west/kustomization.yaml
```

## Step 3: Adjust Design Prompts

Update `src/pool-design/prompts.py` to include region-specific guidance:

- Texas: consider larger lots, different soil, no screen enclosures
- Arizona: desert landscaping, extreme heat considerations
- California: drought restrictions, earthquake codes

## Step 4: Bootstrap Flux on New Cluster

```bash
az k8s-configuration flux create \
  --resource-group azl-pools-rg \
  --cluster-name azl-pools-west \
  --cluster-type connectedClusters \
  --name azl-pools-gitops-west \
  --namespace flux-system \
  --scope cluster \
  --url https://github.com/mgodfre3/AzL-Pools \
  --branch main \
  --kustomization name=infra path=./clusters/prod-west/infrastructure.yaml \
  --kustomization name=apps path=./clusters/prod-west/apps.yaml depends_on=infra
```

## Step 5: Scale Nodes

```bash
az aksarc update \
  --resource-group azl-pools-rg \
  --name azl-pools-west \
  --node-count 3
```

## Recommended Expansion Order

| Phase | Region | Est. $1M+ Homes | Pool Demand |
|-------|--------|-----------------|-------------|
| 1 | FL Tri-County (done) | ~80,000 | Very High |
| 2 | FL statewide | ~30,000 | Very High |
| 3 | TX (Houston, Dallas, Austin) | ~50,000 | High |
| 4 | AZ (Phoenix, Scottsdale) | ~25,000 | Very High |
| 5 | CA (LA, San Diego) | ~100,000 | High |
| 6 | NV, GA, NC | ~20,000 | Moderate |
