# Bot Account Setup (Local Docker Wiki)

## Prerequisites

- Docker and docker-compose installed
- Wiki7 Docker environment available (`Wiki7/docker/`)

## Steps

### 1. Start the local wiki

```bash
cd Wiki7/docker && docker-compose up -d
```

Wait for it to be ready at http://localhost:8080 (first start takes ~30 seconds for DB init).

### 2. Log in as Admin

- Go to http://localhost:8080/index.php/Special:UserLogin
- Username: `Admin`
- Password: `AdminPass1234` (from docker-compose.yml)

### 3. Create a bot account

- Go to http://localhost:8080/index.php/Special:CreateAccount
- Username: `Wiki7Bot`
- Password: choose a password (e.g., `BotPass1234`)

### 4. Grant bot rights

- Go to http://localhost:8080/index.php/Special:UserRights
- Enter `Wiki7Bot` in the username field
- Add to groups: **bot**, **sysop** (sysop gives full edit rights for testing)
- Click Save

### 5. Configure environment variables

```bash
export WIKI_URL="localhost:8080"
export WIKI_BOT_USER="Wiki7Bot"
export WIKI_BOT_PASS="BotPass1234"
```

### 6. Run the pipeline

```bash
cd Wiki7/data

# Dry run first (no wiki writes)
python run_pipeline.py --season 2024 --dry-run -v

# Real run
python run_pipeline.py --season 2024 -v

# Multi-season
python run_pipeline.py --seasons 2015-2025 -v
```

## Troubleshooting

- **"Anonymous users cannot edit"**: Bot account not set up or env vars not exported
- **"Login failed"**: Check WIKI_BOT_USER/WIKI_BOT_PASS match what you created
- **Connection refused**: Docker wiki not running, check `docker-compose ps`
- **Cargo table errors**: Run `php maintenance/run.php cargoRecreateData` inside the container
