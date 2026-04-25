.PHONY: dev-up dev-down lint test func-start deploy-infra deploy-func package-marketplace

# Local development
dev-up:
	docker compose up -d

dev-down:
	docker compose down

# Start Azure Functions locally
func-start:
	cd functions && func start

# Lint
lint:
	cd functions && ruff check .

# Run tests
test:
	cd functions && pytest tests/ -v

# Deploy infrastructure
deploy-infra:
	az deployment group create -g azl-pools-rg -f infra/main.bicep

# Deploy functions
deploy-func:
	cd functions && func azure functionapp publish $(FUNC_APP_NAME)

# Package for marketplace
package-marketplace:
	cd marketplace && zip -r ../azl-pools-marketplace.zip arm/ ui/ manifest.json
