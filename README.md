# Wiki7 (ויקישבע)

A fan wiki for Hapoel Beer Sheva FC, built on MediaWiki and deployed at [wiki7.co.il](https://wiki7.co.il).

## Project Structure

| Directory | Purpose | Stack |
|-----------|---------|-------|
| `docker/` | MediaWiki + Wiki7 skin (local dev & production image) | PHP, Mustache, LESS, JS, Docker |
| `cdk/` | AWS infrastructure (CDK stacks) | TypeScript, Python (Lambda) |
| `data/` | Data pipeline (Transfermarkt scraper) | Python (Scrapy, Pydantic) |
| `docs/` | Documentation | Markdown |

## Quick Start

See [docs/SETUP.md](docs/SETUP.md) for full instructions.

```bash
git clone <repo> && cd Wiki7
git submodule update --init --recursive
cp .env.example .env  # Fill in values
cd docker && docker compose up -d
# Visit http://localhost:8080
```

## Tech Stack

- **MediaWiki 1.45.1** — wiki engine
- **Wiki7 skin** — custom skin based on Citizen v3.1.0
- **MariaDB 11.4** — database
- **Docker** — local development and production image
- **AWS CDK** — infrastructure as code
- **Scrapy** — data pipeline for Transfermarkt scraping

## Documentation

- [SETUP.md](docs/SETUP.md) — local development setup
- [SKIN-DEVELOPMENT.md](docs/SKIN-DEVELOPMENT.md) — Wiki7 skin development guide
- [INFRASTRUCTURE.md](docs/INFRASTRUCTURE.md) — AWS infrastructure overview
- [data/README.md](data/README.md) — data pipeline documentation

## Current Status

Active development. Deployed at [wiki7.co.il](https://wiki7.co.il).
