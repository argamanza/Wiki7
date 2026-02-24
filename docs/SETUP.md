# Wiki7 Local Development Setup

This guide covers everything needed to run the Wiki7 (Hapoel Beer Sheva FC fan wiki) locally for development.

---

## Prerequisites

Install the following before proceeding:

| Tool | Version | Purpose |
|------|---------|---------|
| [Docker](https://docs.docker.com/get-docker/) & Docker Compose | Docker 24+ / Compose v2+ | Runs MediaWiki, MariaDB, and Adminer containers |
| [Git](https://git-scm.com/) | 2.30+ | Source control; needed for submodule support |
| [Node.js](https://nodejs.org/) | 18 LTS or 20 LTS | Skin development tooling and AWS CDK |
| [Python](https://www.python.org/) | 3.12 | Data pipeline (Transfermarkt scraper) |
| [Poetry](https://python-poetry.org/) | 1.7+ | Python dependency management for data pipeline |

---

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/<org>/Wiki7.git && cd Wiki7

# 2. Initialize submodules (MediaWiki extensions, etc.)
git submodule update --init --recursive

# 3. Create your local environment file
cp .env.example .env
# Then edit .env and fill in real values (see "Environment Variables" below)

# 4. Start all services
cd docker
docker compose up -d

# 5. Verify the wiki is running
#    Open http://localhost:8080 in your browser

# 6. (Optional) Access the database admin UI
#    Open http://localhost:8081 (Adminer)
#    Server: db | Username: wikiuser | Password: <your MYSQL_PASSWORD> | Database: wikidb
```

---

## Environment Variables

The `.env` file lives at the repository root. Copy `.env.example` to `.env` and fill in each value:

| Variable | Description | How to Generate / Notes |
|----------|-------------|------------------------|
| `MEDIAWIKI_DB_PASSWORD` | Password for the MediaWiki database user (`wikiuser`). Used by the MediaWiki container to connect to MariaDB. | Pick any strong password. For local dev, a simple value like `devpass` is fine. |
| `MYSQL_PASSWORD` | Password for the MariaDB `wikiuser` account. | **Must match** `MEDIAWIKI_DB_PASSWORD` so MediaWiki can authenticate. |
| `MYSQL_ROOT_PASSWORD` | Root password for the MariaDB instance. | Can be the same as the above for local dev, but use a distinct value in production. |
| `WG_SECRET_KEY` | 64-character hex string used by MediaWiki for session signing and CSRF tokens. | Generate with: `openssl rand -hex 32` |
| `WG_UPGRADE_KEY` | 16-character hex string used to access the MediaWiki web installer/upgrader. | Generate with: `openssl rand -hex 8` |
| `SCRAPERAPI_KEY` | API key for [ScraperAPI](https://www.scraperapi.com/), used by the Transfermarkt data scraper. | Optional for wiki development. Only needed if you are working on the data pipeline. |

---

## Service Architecture (Local Dev)

When you run `docker compose up -d` from the `docker/` directory, three containers are created:

```
┌──────────────────────────────────────────────────────────────┐
│  Host machine                                                │
│                                                              │
│  http://localhost:8080 ──► mediawiki container (Apache+PHP)  │
│  http://localhost:8081 ──► adminer container (DB admin UI)   │
│                                                              │
│  mediawiki ──► db container (MariaDB 11.4, port 3306)        │
└──────────────────────────────────────────────────────────────┘
```

| Container | Image | Port | Description |
|-----------|-------|------|-------------|
| `mediawiki` | Custom (built from `docker/Dockerfile`) | 8080 -> 80 | MediaWiki with the Wiki7 skin, PHP, and Apache |
| `db` | `mariadb:11.4` | 3306 (internal only) | MariaDB database for all wiki data |
| `adminer` | `adminer` | 8081 -> 8080 | Lightweight database management UI |

### Volumes

The following host directories are mounted into the `mediawiki` container for live editing:

| Host Path | Container Path | Purpose |
|-----------|---------------|---------|
| `docker/images/` | `/var/www/html/images` | Wiki uploaded files |
| `docker/assets/` | `/var/www/html/assets` | Custom static assets |
| `docker/skins/` | `/var/www/html/skins` | MediaWiki skins (including Wiki7) |

The `db_data` named volume persists MariaDB data between container restarts.

---

## Common Tasks

All commands below should be run from the `docker/` directory.

```bash
# Restart all services
docker compose restart

# View live logs for the mediawiki container
docker compose logs -f mediawiki

# Stop all services (data is preserved)
docker compose down

# Reset database (DELETES ALL DATA!)
docker compose down -v

# Run a MediaWiki maintenance script
docker compose exec mediawiki php maintenance/run.php <script>
# Example: docker compose exec mediawiki php maintenance/run.php update

# Rebuild containers after Dockerfile changes
docker compose up -d --build
```

---

## Developing the Wiki7 Skin

The custom Wiki7 skin source lives at `docker/skins/Wiki7/` and is bind-mounted into the container.

- **PHP / Mustache template changes** take effect immediately on page reload.
- **LESS / CSS changes** require a ResourceLoader cache purge. Append `?action=purge` to any wiki page URL to flush the cache, or do a hard refresh.
- For full skin development documentation, see `docs/SKIN-DEVELOPMENT.md`.

---

## CDK Infrastructure

The AWS CDK project lives in the `cdk/` directory.

```bash
cd cdk
npm install
npx cdk synth
```

This synthesizes the CloudFormation templates without deploying. See `docs/INFRASTRUCTURE.md` for full infrastructure documentation.

---

## Data Pipeline

The Transfermarkt scraper and data pipeline live in the `data/` directory.

```bash
cd data
poetry install
```

This installs all Python dependencies into a virtual environment managed by Poetry. See `data/README.md` for usage instructions and pipeline details.

---

## Troubleshooting

### Port 8080 already in use

Another process is bound to port 8080. Either stop that process or change the port mapping in `docker/docker-compose.yml`:

```yaml
ports:
  - "9090:80"   # use port 9090 instead
```

### Permission errors on uploaded images

The `images/` volume may have incorrect ownership. Fix with:

```bash
docker compose exec mediawiki chown -R www-data:www-data /var/www/html/images
```

### Submodules are empty

If extension or skin directories are empty after cloning, initialize submodules:

```bash
git submodule update --init --recursive
```

### "Table not found" errors

The database schema may be outdated. Run the MediaWiki updater:

```bash
docker compose exec mediawiki php maintenance/run.php update
```

### Container won't start

Check the database container logs first -- MariaDB initialization errors are the most common cause:

```bash
docker compose logs db
```

If MariaDB fails to initialize, try removing the volume and starting fresh:

```bash
docker compose down -v
docker compose up -d
```
