.PHONY: dev-up dev-down lint test build

# Local development
dev-up:
	docker compose up -d

dev-down:
	docker compose down

# Lint all Python services
lint:
	cd src/data-ingestion && ruff check .
	cd src/pool-detection && ruff check .
	cd src/pool-design && ruff check .
	cd src/contact-enrichment && ruff check .

# Run all tests
test:
	cd src/data-ingestion && pytest
	cd src/pool-detection && pytest
	cd src/pool-design && pytest
	cd src/contact-enrichment && pytest

# Build all container images
build:
	docker build -t azlpoolsacr.azurecr.io/data-ingestion:dev ./src/data-ingestion/
	docker build -t azlpoolsacr.azurecr.io/pool-detection:dev ./src/pool-detection/
	docker build -t azlpoolsacr.azurecr.io/pool-design:dev ./src/pool-design/
	docker build -t azlpoolsacr.azurecr.io/contact-enrichment:dev ./src/contact-enrichment/
	docker build -t azlpoolsacr.azurecr.io/dashboard:dev ./src/dashboard/
