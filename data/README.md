# Wiki7 Data Pipeline

## Overview

The data pipeline scrapes **Transfermarkt** for Hapoel Beer Sheva FC (club ID: 2976) player and match data, normalizes it into structured JSONL files, and imports it into the wiki7.co.il MediaWiki instance. The pipeline is fully orchestrated via a single `run_pipeline.py` script.

**Target data:**
- Squad rosters (active + loaned players)
- Player profiles (facts, positions, market value history, transfer history)
- Season fixtures (results, attendance, formation)
- Match reports (lineups, goals, substitutions, cards, penalties)

---

## Architecture

```
Transfermarkt.com
       |
       v
+---------------------+     +---------------------+     +---------------------+
|  Scrapy Spiders     |     |  Normalization       |     |  Wiki Import        |
|  (tmk-scraper/)     |---->|  Pipeline            |---->|  (wiki_import/)     |
|                     |     |  (data_pipeline/)    |     |                     |
|  squad -> player    |     |                      |     |  import_players     |
|  fixtures -> match  |     |  normalize_enrich    |     |  import_matches     |
|                     |     |  generate_mapping    |     |  import_templates   |
|  Output: JSON files |     |  apply_hebrew        |     |  (Cargo + pages)    |
|  in output/         |     |                      |     |                     |
+---------------------+     |  Output: JSONL files |     |  Uses mwclient +   |
                             |  in output/          |     |  Jinja2 templates  |
                             +---------------------+     +---------------------+
                                                                  |
                                                                  v
                                                         MediaWiki (wiki7.co.il)

Orchestrated by: run_pipeline.py (scrape -> normalize -> import)
```

The spiders run in a specific order because later spiders depend on the output of earlier ones:
1. `squad` -- Scrapes the squad page to get player names and profile URLs
2. `player` -- Reads `output/squad.json`, then scrapes each player's profile page, market value API, and transfer history API
3. `fixtures` -- Scrapes the season fixtures page to get match results and report URLs
4. `match` -- Reads `output/fixtures.json`, then scrapes each match report page for lineups, goals, cards, and substitutions

---

## Quick Start

### Prerequisites

- Python 3.12+
- [Poetry](https://python-poetry.org/) package manager
- A ScraperAPI key (optional but recommended -- Transfermarkt blocks direct scraping)

### Installation

```bash
cd data
poetry install
```

### Full Pipeline (Dry Run)

Preview what would be imported without actually writing to MediaWiki:

```bash
poetry run python run_pipeline.py --season 2024 --dry-run
```

### Full Pipeline (Live)

```bash
export SCRAPERAPI_KEY="your_key_here"
export WIKI_URL="wiki7.co.il"
export WIKI_BOT_USER="Bot@username"
export WIKI_BOT_PASS="bot_password"
poetry run python run_pipeline.py --season 2024
```

### Skip Scraping (Normalize + Import Only)

```bash
poetry run python run_pipeline.py --skip-scrape --dry-run
```

---

## Pipeline Stages

### Stage 1: Scraping (Scrapy Spiders)

#### `squad` Spider
**File:** `tmk-scraper/tmk_scraper/spiders/squad_spider.py`

Scrapes the Hapoel Beer Sheva squad page for a given season. Also follows a link to scrape loaned-out players.

**Input:** Season argument (default: `2024`)
**URL pattern:** `https://www.transfermarkt.com/hapoel-beer-sheva/kader/verein/2976/saison_id/{season}`
**Output fields:**
| Field | Type | Description |
|-------|------|-------------|
| `name_english` | string | Player name as displayed on Transfermarkt |
| `profile_url` | string | Full URL to the player's Transfermarkt profile |
| `number` | string | Jersey number (or `"-"` if unavailable) |
| `season` | string | Season year |
| `loaned` | boolean | Whether the player is on loan |

#### `player` Spider
**File:** `tmk-scraper/tmk_scraper/spiders/player_spider.py`

Reads `output/squad.json` and scrapes each player's profile page. Makes three requests per player:
1. Profile page (HTML) -- extracts biographical facts and positions
2. Market value API (`/ceapi/marketValueDevelopment/graph/{id}`) -- JSON endpoint
3. Transfer history API (`/ceapi/transferHistory/list/{id}`) -- JSON endpoint

**Input:** Requires `output/squad.json` from the squad spider
**Output fields (extends squad data):**
| Field | Type | Description |
|-------|------|-------------|
| `facts` | object | Key-value biographical data (date of birth, citizenship, height, foot, etc.) |
| `positions.main` | string | Primary playing position |
| `positions.other` | list | Other positions |
| `market_value_history` | list | Array of `{date, value, team}` records |
| `transfers` | list | Array of `{season, date, from, to, fee}` records |

#### `fixtures` Spider
**File:** `tmk-scraper/tmk_scraper/spiders/fixtures_spider.py`

Scrapes the season fixture list, grouped by competition.

**Input:** Season argument (default: `2024`)
**URL pattern:** `https://www.transfermarkt.com/hapoel-beer-sheva/spielplandatum/verein/2976/saison_id/{season}`
**Output fields:**
| Field | Type | Description |
|-------|------|-------------|
| `competition` | string | Competition name (e.g., "Israeli Premier League") |
| `matchday` | string | Matchday number |
| `date` | string | Match date |
| `time` | string | Kickoff time |
| `venue` | string | Home (H) or Away (A) |
| `opponent` | string | Opponent team name |
| `system_of_play` | string | Formation used (e.g., "4-3-3") |
| `attendance` | string | Match attendance |
| `result` | string | Score (e.g., "2:1") |
| `match_report_url` | string | URL to the detailed match report |

#### `match` Spider
**File:** `tmk-scraper/tmk_scraper/spiders/match_spider.py`

Reads `output/fixtures.json` and scrapes each match report page for detailed event data.

**Input:** Requires `output/fixtures.json` from the fixtures spider
**Output fields (extends fixture data):**
| Field | Type | Description |
|-------|------|-------------|
| `home_lineup` | list/object | Starting lineup for the home team |
| `away_lineup` | list/object | Starting lineup for the away team |
| `goals` | list | Array of `{minute, score, scorer, assist, team, details}` |
| `substitutions` | list | Array of `{team, minute, player_in, player_out, reason}` |
| `cards` | list | Array of `{team, minute, player, card, reason}` |
| `penalties` | list/null | Penalty shootout details (if applicable) |
| `manager_sanctions` | list | Manager yellow/red cards |

### Stage 2: Normalization

**Directory:** `data_pipeline/`

Transforms raw spider JSON into structured, validated JSONL using Pydantic schemas.

```bash
# Standalone usage (usually called via run_pipeline.py):
poetry run python -m data_pipeline.normalize_enrich_players
```

**Produces:**
- `data_pipeline/output/players.jsonl` -- Normalized player records
- `data_pipeline/output/transfers.jsonl` -- Transfer history records
- `data_pipeline/output/market_values.jsonl` -- Market value history records

#### Hebrew Enrichment (Optional)

```bash
# Generate a mapping stub with all unique values needing translation
poetry run python -m data_pipeline.generate_mapping_stub

# Manually fill in Hebrew values in data_pipeline/output/mappings.he.yaml

# Apply the Hebrew mapping
poetry run python -m data_pipeline.apply_hebrew_mapping
```

This produces `data_pipeline/output/players.he.jsonl` with Hebrew-enriched data.

### Stage 3: Wiki Import

**Directory:** `wiki_import/`

Creates/updates MediaWiki pages from normalized data using `mwclient` and Jinja2 templates.

**Modules:**
| Module | Purpose |
|--------|---------|
| `import_players.py` | Creates/updates player infobox pages |
| `import_matches.py` | Creates/updates match report pages |
| `import_templates.py` | Creates Cargo table templates, squad pages, and transfer pages |

**Templates (Jinja2):**
| Template | Purpose |
|----------|---------|
| `templates/player_page.j2` | Player infobox + career history + market values |
| `templates/match_report.j2` | Match report with lineups, goals, cards, subs |
| `templates/squad_table.j2` | Season squad table |
| `templates/transfer_table.j2` | Season incoming/outgoing transfer tables |

**Features:**
- **Idempotent:** Pages are only edited if content has actually changed (MD5 comparison)
- **Dry-run mode:** Preview all changes without writing to the wiki
- **Retry logic:** Automatic retries with exponential backoff for API errors
- **Cargo tables:** Defines structured data tables for MediaWiki's Cargo extension

---

## Orchestration CLI

The `run_pipeline.py` script chains all three stages:

```
Usage: run_pipeline.py [OPTIONS]

Options:
  --season TEXT       Season year to process (default: 2024)
  --dry-run           Preview import without writing to wiki
  --skip-scrape       Skip the scraping step
  --skip-normalize    Skip the normalization step
  --skip-import       Skip the wiki import step
  --wiki-url TEXT     MediaWiki site URL (or set WIKI_URL env var)
  -v, --verbose       Enable debug logging
  --help              Show this message and exit.
```

---

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SCRAPERAPI_KEY` | ScraperAPI proxy key for Transfermarkt scraping | For scraping |
| `WIKI_URL` | MediaWiki site hostname (e.g., `wiki7.co.il`) | For live import |
| `WIKI_BOT_USER` | MediaWiki bot username | For live import |
| `WIKI_BOT_PASS` | MediaWiki bot password | For live import |

### Scrapy Settings

**File:** `tmk-scraper/tmk_scraper/settings.py`

| Setting | Value | Description |
|---------|-------|-------------|
| `USE_SCRAPERAPI` | `True` | Route requests through ScraperAPI proxy |
| `SCRAPERAPI_KEY` | `os.environ['SCRAPERAPI_KEY']` | API key from environment variable |
| `CONCURRENT_REQUESTS` | `5` | Maximum concurrent requests |
| `RETRY_TIMES` | `5` | Number of retries on failure |
| `RETRY_HTTP_CODES` | `[500, 503, 504, 522, 524, 408, 429]` | HTTP codes that trigger retry |
| `FEED_FORMAT` | `json` | Default output format |
| `FEED_EXPORT_ENCODING` | `utf-8` | Output encoding |
| `LOG_LEVEL` | `DEBUG` | Logging verbosity |

When ScraperAPI is disabled, auto-throttling is enabled with a 3-second download delay.

### Dependencies

Defined in `pyproject.toml`:
- `scrapy` ^2.13.0 -- Web scraping framework
- `scrapy-fake-useragent` ^1.4.4 -- User-Agent rotation
- `pydantic` ^2.11.5 -- Data validation and schemas
- `tqdm` ^4.67.1 -- Progress bars
- `python-dateutil` ^2.9.0 -- Date parsing
- `pycountry` ^24.6.1 -- Country name normalization
- `pyyaml` ^6.0.2 -- YAML file handling (for Hebrew mappings)
- `mwclient` ^0.11.0 -- MediaWiki API client
- `jinja2` ^3.1 -- Template rendering for wiki pages
- `click` ^8.1 -- CLI argument parsing
- `tenacity` ^9.0 -- Retry logic with exponential backoff

---

## Output Files and Schemas

### Raw Spider Output (JSON)

| File | Spider | Description |
|------|--------|-------------|
| `tmk-scraper/output/squad.json` | squad | Array of player stubs with profile URLs |
| `tmk-scraper/output/players.json` | player | Array of full player profiles |
| `tmk-scraper/output/fixtures.json` | fixtures | Array of season fixture records |
| `tmk-scraper/output/matches.json` | match | Array of detailed match reports |

### Normalized Output (JSONL)

| File | Description |
|------|-------------|
| `data_pipeline/output/players.jsonl` | One JSON object per line, normalized player data |
| `data_pipeline/output/transfers.jsonl` | One JSON object per line, transfer records |
| `data_pipeline/output/market_values.jsonl` | One JSON object per line, market value records |
| `data_pipeline/output/players.he.jsonl` | Hebrew-enriched player data |
| `data_pipeline/output/mappings.he.yaml` | Hebrew translation mapping file |

### Pydantic Schemas

Defined in `data_pipeline/schemas.py`:

**Player:**
```python
class Player(BaseModel):
    id: str                          # Transfermarkt player ID
    name_english: str                # English name
    name_hebrew: Optional[str]       # Hebrew name (from "Name in home country" if Hebrew)
    nationality: Optional[List[str]] # List of nationalities (standardized)
    birth_date: Optional[date]       # Date of birth
    birth_place: Optional[str]       # Place of birth
    main_position: Optional[str]     # Primary position
    current_squad: bool              # True if not loaned out
    current_jersey_number: Optional[int]  # Jersey number
    homegrown: bool                  # True if came through Beer Sheva youth
    retired: bool                    # True if last transfer "to" contains "retired"
```

**Transfer:**
```python
class Transfer(BaseModel):
    player_id: str       # Transfermarkt player ID
    season: str          # Transfer season
    transfer_date: str   # Date of transfer
    from_club: str       # Origin club
    to_club: str         # Destination club
    fee: str             # Transfer fee (raw string, e.g., "Free transfer", "Loan")
    loan: bool           # True if fee contains "loan"
```

**MarketValue:**
```python
class MarketValue(BaseModel):
    player_id: str    # Transfermarkt player ID
    value_date: str   # Date of valuation
    value: str        # Market value (raw string)
    team: str         # Team at time of valuation
```

---

## Running Spiders Individually

If you need to run spiders manually (outside the orchestrator):

```bash
cd data/tmk-scraper

# Step 1: Scrape the squad roster
poetry run scrapy crawl squad -a season=2024 -o output/squad.json

# Step 2: Scrape player profiles (depends on output/squad.json)
poetry run scrapy crawl player -o output/players.json

# Step 3: Scrape season fixtures
poetry run scrapy crawl fixtures -a season=2024 -o output/fixtures.json

# Step 4: Scrape match reports (depends on output/fixtures.json)
poetry run scrapy crawl match -o output/matches.json
```

---

## Known Limitations

1. **Scrapy is over-engineered for single-team scraping:** The Scrapy framework adds significant complexity (middlewares, pipelines, settings, items) for what is essentially scraping data for a single team. A simpler approach with `requests` + `BeautifulSoup` would achieve the same result with less overhead.

2. **Sequential spider dependency:** The `player` spider reads `output/squad.json` and the `match` spider reads `output/fixtures.json`. The orchestrator (`run_pipeline.py`) enforces this order, but when running spiders manually you must follow the correct sequence.

3. **Items class is unused:** `tmk_scraper/items.py` defines an empty `TmkScraperItem` class that is never used. All spiders yield plain dictionaries.

4. **Pipeline class is a no-op:** `tmk_scraper/pipelines.py` defines `TmkScraperPipeline.process_item()` which simply returns the item unchanged and is not registered in settings.

---

## Legal Note

Scraping Transfermarkt violates their [Terms of Service](https://www.transfermarkt.com/intern/anb). While this is common practice among fan wikis and football data projects, and the data is used strictly for a non-commercial fan wiki, be aware of the legal risk. Transfermarkt has been known to pursue legal action against commercial scrapers. Use at your own discretion and consider contributing to the Transfermarkt community in return.
