# Wiki7 Data Pipeline

## Overview

The data pipeline scrapes **Transfermarkt** for Hapoel Beer Sheva FC (club ID: 2976) player and match data, normalizes it into structured JSONL files, and optionally enriches it with Hebrew translations. The pipeline is designed to feed data into the wiki7.co.il MediaWiki instance, though the final import step has not been implemented yet.

**Target data:**
- Squad rosters (active + loaned players)
- Player profiles (facts, positions, market value history, transfer history)
- Season fixtures (results, attendance, formation)
- Match reports (lineups, goals, substitutions, cards, penalties)

---

## Architecture

```
Transfermarkt.com
       │
       ▼
┌─────────────────────┐     ┌─────────────────────┐
│  Scrapy Spiders     │     │  Normalization       │
│  (tmk-scraper/)     │────▶│  Pipeline            │
│                     │     │  (data_pipeline/)    │
│  squad → player     │     │                      │
│  fixtures → match   │     │  normalize_enrich    │
│                     │     │  generate_mapping    │
│  Output: JSON files │     │  apply_hebrew        │
│  in output/         │     │                      │
└─────────────────────┘     │  Output: JSONL files │
                            │  in output/          │
                            └──────────┬───────────┘
                                       │
                                       ▼
                              ┌─────────────────┐
                              │  (Future)        │
                              │  Wiki Import     │
                              │  via MediaWiki   │
                              │  API / mwclient  │
                              │                  │
                              │  NOT IMPLEMENTED │
                              └─────────────────┘
```

The spiders run in a specific order because later spiders depend on the output of earlier ones:
1. `squad` -- Scrapes the squad page to get player names and profile URLs
2. `player` -- Reads `output/squad.json`, then scrapes each player's profile page, market value API, and transfer history API
3. `fixtures` -- Scrapes the season fixtures page to get match results and report URLs
4. `match` -- Reads `output/fixtures.json`, then scrapes each match report page for lineups, goals, cards, and substitutions

---

## Spider Descriptions

### 1. `squad` Spider
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

### 2. `player` Spider
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

### 3. `fixtures` Spider
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

### 4. `match` Spider
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

---

## Running the Pipeline

### Prerequisites

- Python 3.12+
- [Poetry](https://python-poetry.org/) package manager
- A ScraperAPI key (optional but recommended -- Transfermarkt blocks direct scraping)

### Installation

```bash
cd data
poetry install
```

### Setting Up ScraperAPI (Optional)

Export your ScraperAPI key as an environment variable:

```bash
export SCRAPERAPI_KEY="your_key_here"
```

If no key is set, spiders will attempt direct requests to Transfermarkt (likely to be blocked). To disable ScraperAPI, set `USE_SCRAPERAPI = False` in `tmk-scraper/tmk_scraper/settings.py`.

### Running Spiders

Spiders must be run in order from the `tmk-scraper/` directory:

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

The `-a season=YYYY` argument sets the season (defaults to 2024). The `-o` flag specifies the output file.

### Running the Normalization Pipeline

After scraping, normalize the raw player data into structured JSONL:

```bash
cd data
poetry run python -m data_pipeline.normalize_enrich_players
```

This reads `tmk-scraper/output/players.json` and produces three files in `data_pipeline/output/`:
- `players.jsonl` -- Normalized player records
- `transfers.jsonl` -- Transfer history records
- `market_values.jsonl` -- Market value history records

### Hebrew Enrichment (Optional)

To add Hebrew translations for player names, positions, clubs, and nationalities:

```bash
cd data

# Step 1: Generate a mapping stub with all unique values needing translation
poetry run python -m data_pipeline.generate_mapping_stub

# Step 2: Manually fill in Hebrew values in output/mappings.he.yaml

# Step 3: Apply the Hebrew mapping
poetry run python -m data_pipeline.apply_hebrew_mapping
```

This produces `data_pipeline/output/players.he.jsonl` with Hebrew-enriched data.

---

## Configuration

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

The `scrapy-fake-useragent` middleware rotates User-Agent strings to reduce detection risk.

### Dependencies

Defined in `pyproject.toml`:
- `scrapy` ^2.13.0 -- Web scraping framework
- `scrapy-fake-useragent` ^1.4.4 -- User-Agent rotation
- `pydantic` ^2.11.5 -- Data validation and schemas
- `tqdm` ^4.67.1 -- Progress bars
- `python-dateutil` ^2.9.0 -- Date parsing
- `pycountry` ^24.6.1 -- Country name normalization
- `pyyaml` ^6.0.2 -- YAML file handling (for Hebrew mappings)

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

## Known Limitations

1. **Missing "last mile":** There is no code to import the normalized data into MediaWiki. The pipeline produces JSONL files, but nothing creates or updates wiki pages from them. A tool like `mwclient` or `pywikibot` would be needed to complete this.

2. **Scrapy is over-engineered for single-team scraping:** The Scrapy framework adds significant complexity (middlewares, pipelines, settings, items) for what is essentially scraping data for a single team. A simpler approach with `requests` + `BeautifulSoup` in ~180 lines would achieve the same result with less overhead.

3. **Broken team matching in match spider:** The `resolve_team_key()` method in `match_spider.py` tries to match team names against `home_team` and `away_team` fields in the match data, but the fixtures spider does not produce these fields. The fallback logic (first team seen = home, second = away) is fragile.

4. **Sequential spider dependency:** The `player` spider reads `output/squad.json` and the `match` spider reads `output/fixtures.json`. These files must exist before running the dependent spider. There is no orchestration or pipeline runner to enforce this order.

5. **docker-compose.yml references non-existent directory:** The `docker-compose.yml` in `data/` tries to build from a `transfermarkt-api/` directory that does not exist in the repository. This file appears to be a leftover from an earlier architecture.

6. **No tests:** There are zero test files for any part of the data pipeline -- no spider tests, no schema tests, no normalization tests.

7. **Items class is unused:** `tmk_scraper/items.py` defines an empty `TmkScraperItem` class that is never used. All spiders yield plain dictionaries.

8. **Pipeline class is a no-op:** `tmk_scraper/pipelines.py` defines `TmkScraperPipeline.process_item()` which simply returns the item unchanged and is not registered in settings.

---

## Legal Note

Scraping Transfermarkt violates their [Terms of Service](https://www.transfermarkt.com/intern/anb). While this is common practice among fan wikis and football data projects, and the data is used strictly for a non-commercial fan wiki, be aware of the legal risk. Transfermarkt has been known to pursue legal action against commercial scrapers. Use at your own discretion and consider contributing to the Transfermarkt community in return.
