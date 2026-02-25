.PHONY: help setup docker-up docker-down docker-logs docker-restart docker-reset test lint cdk-synth cdk-diff pipeline

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# --- Setup ---
setup: ## Initial project setup
	cp -n .env.example .env || true
	git submodule update --init --recursive
	cd docker && docker compose build

# --- Docker (Local Development) ---
docker-up: ## Start local development environment
	cd docker && docker compose up -d

docker-down: ## Stop local development environment
	cd docker && docker compose down

docker-logs: ## Follow logs from all containers
	cd docker && docker compose logs -f

docker-restart: ## Restart all containers
	cd docker && docker compose restart

docker-reset: ## Reset everything (WARNING: deletes database!)
	cd docker && docker compose down -v
	cd docker && docker compose up -d --build

docker-shell: ## Open a shell in the MediaWiki container
	cd docker && docker compose exec mediawiki bash

docker-update-db: ## Run MediaWiki database update
	cd docker && docker compose exec mediawiki php maintenance/run.php update

# --- Testing ---
test: ## Run all tests
	@echo "Running data pipeline tests..."
	cd data && python -m pytest --tb=short -v || true
	@echo "Running CDK tests..."
	cd cdk && npm test || true

lint: ## Run all linters
	@echo "Running Python linter..."
	cd data && ruff check . || true

# --- CDK Infrastructure ---
cdk-synth: ## Synthesize CDK stacks
	cd cdk && npx cdk synth

cdk-diff: ## Show CDK diff against deployed stacks
	cd cdk && npx cdk diff

cdk-deploy: ## Deploy CDK stacks (requires AWS credentials)
	cd cdk && npx cdk deploy --all

# --- Data Pipeline ---
pipeline-install: ## Install data pipeline dependencies
	cd data && pip install poetry && poetry install

pipeline-scrape: ## Run the full scraping pipeline
	cd data && python run_pipeline.py --skip-normalize --skip-import

pipeline-normalize: ## Run data normalization
	cd data && python run_pipeline.py --skip-scrape --skip-import

pipeline-dry-run: ## Preview wiki import (no actual changes)
	cd data && python run_pipeline.py --skip-scrape --dry-run -v

pipeline-import: ## Import data to wiki (requires WIKI_URL)
	cd data && python run_pipeline.py --skip-scrape -v
