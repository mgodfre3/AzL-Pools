# Flux GitOps Bootstrap Runbook

## Prerequisites

- Arc-enabled AKS cluster is running (see [cluster-bootstrap.md](./cluster-bootstrap.md))
- `kubectl` context set to the cluster
- GitHub repo `AzL-Pools` is accessible

## Option A: Azure CLI Flux Extension (Recommended for Arc)

```bash
az k8s-configuration flux create \
  --resource-group azl-pools-rg \
  --cluster-name azl-pools-cluster \
  --cluster-type connectedClusters \
  --name azl-pools-gitops \
  --namespace flux-system \
  --scope cluster \
  --url https://github.com/mgodfre3/AzL-Pools \
  --branch main \
  --kustomization name=infra path=./clusters/prod/infrastructure.yaml prune=true \
  --kustomization name=apps path=./clusters/prod/apps.yaml prune=true depends_on=infra
```

## Option B: Flux CLI Bootstrap

```bash
# Install Flux CLI
curl -s https://fluxcd.io/install.sh | sudo bash

# Bootstrap
flux bootstrap github \
  --owner=mgodfre3 \
  --repository=AzL-Pools \
  --branch=main \
  --path=./clusters/prod \
  --personal
```

## Verify

```bash
# Check Flux controllers
kubectl get pods -n flux-system

# Check Kustomizations
kubectl get kustomizations -A

# Check HelmReleases
kubectl get helmreleases -A

# Watch reconciliation
flux get kustomizations --watch
```

## Create Secrets

Before apps can start, create the required secrets:

```bash
# Database credentials
kubectl create secret generic db-credentials \
  -n pool-prospect \
  --from-literal=username=poolprospect \
  --from-literal=password=<YOUR_PASSWORD> \
  --from-literal=url=postgresql://poolprospect:<PASSWORD>@postgres-svc:5432/poolprospect

# API keys
kubectl create secret generic api-keys \
  -n pool-prospect \
  --from-literal=attom=<ATTOM_API_KEY> \
  --from-literal=bing-maps=<BING_MAPS_KEY> \
  --from-literal=melissa=<MELISSA_API_KEY>
```

For GitOps-managed secrets, use Sealed Secrets:

```bash
# Install kubeseal
brew install kubeseal

# Seal a secret
kubeseal --format yaml < secret.yaml > sealed-secret.yaml
# Commit sealed-secret.yaml to the repo
```

## Troubleshooting

```bash
# Check Flux logs
kubectl logs -n flux-system deployment/source-controller
kubectl logs -n flux-system deployment/kustomize-controller

# Force reconciliation
flux reconcile kustomization infrastructure
flux reconcile kustomization apps-data-ingestion
```
