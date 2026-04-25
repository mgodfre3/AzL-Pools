# Cluster Bootstrap Runbook

## Prerequisites

- Azure subscription with Owner/Contributor access
- Azure Local (Azure Stack HCI) cluster with certified hardware
  - Minimum: 16+ CPU cores, 64 GB ECC RAM, 500 GB NVMe SSD per node
  - Recommended vendors: Dell AX, Lenovo ThinkAgile MX, HPE ProLiant DX
- Azure CLI v2.60+ installed
- `kubectl` installed

## Step 1: Register Azure Providers

```bash
az provider register --namespace Microsoft.Kubernetes
az provider register --namespace Microsoft.KubernetesConfiguration
az provider register --namespace Microsoft.HybridCompute
```

## Step 2: Create Resource Group

```bash
az group create --name azl-pools-rg --location eastus
```

## Step 3: Create Azure Container Registry

```bash
az acr create --resource-group azl-pools-rg --name azlpoolsacr --sku Standard
```

## Step 4: Create AKS Arc Workload Cluster

```bash
az aksarc create \
  --resource-group azl-pools-rg \
  --name azl-pools-cluster \
  --custom-location <CUSTOM_LOCATION_ID> \
  --vnet-ids <VNET_ID> \
  --control-plane-ip 10.0.1.10 \
  --kubernetes-version 1.28.3 \
  --node-count 3 \
  --node-vm-size Standard_D8s_v3
```

## Step 5: Get Credentials

```bash
az aksarc get-credentials \
  --resource-group azl-pools-rg \
  --name azl-pools-cluster

kubectl get nodes
```

## Step 6: Attach ACR to Cluster

```bash
az aksarc update \
  --resource-group azl-pools-rg \
  --name azl-pools-cluster \
  --attach-acr azlpoolsacr
```

## Step 7: Proceed to Flux Bootstrap

See [flux-bootstrap.md](./flux-bootstrap.md).
