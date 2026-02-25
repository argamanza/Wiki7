# Plan: Test, Complete & Upgrade Wiki7

## Context

**Wiki7** is a fan wiki platform for Hapoel Beer Sheva FC (wiki7.co.il). It's a full-stack project with four major components:

| Component | Location | Stack | Purpose |
|-----------|----------|-------|---------|
| **MediaWiki + Wiki7 Skin** | `docker/` | PHP, Mustache, LESS, JS | The wiki itself — content, UI, user experience |
| **AWS Infrastructure** | `cdk/` | TypeScript (CDK), Python (Lambda) | Production hosting on AWS (ECS, RDS, CloudFront, WAF) |
| **Data Pipeline** | `data/` | Python (Scrapy, Pydantic) | Scrape football data from Transfermarkt, normalize for wiki |
| **Documentation & Config** | root, `docs/` | Markdown, YAML, Docker | Project docs, Docker setup, CI/CD |

### Current State (verified Feb 2026 — full audit, not trusting existing docs)

**Versions — all outdated:**
- MediaWiki 1.43.1 (latest: 1.45.1)
- Wiki7 skin based on Citizen v3.1.0 (latest: v3.13.0 — 12 versions behind)
- MariaDB 10.5 (EOL — latest LTS: 11.4+)
- CDK 2.193.0 with **CDK v1 packages mixed in** (v1 is EOL since June 2023)
- Extensions (Cargo, PageForms): versions unknown, submodules not initialized

**Testing — zero across the entire project:**
- No PHPUnit, no QUnit, no visual regression, no accessibility tests
- CDK test file is 100% commented out
- Data pipeline: 0 test files
- No CI/CD pipeline at all (no `.github/workflows/`)

**Security — critical issues found:**
- Hardcoded secrets in git: `wgSecretKey`, `wgUpgradeKey`, database passwords, ScraperAPI key
- XSS in skin search (highlightTitle), HTML injection in PageHeading
- CDK: CloudFront→ALB uses HTTP (unencrypted), S3 public access not blocked, Fargate has public IPs
- No security headers (.htaccess missing HSTS, CSP, X-Frame-Options)
- RDS: no deletion protection, `RemovalPolicy.DESTROY`, no Multi-AZ

**Documentation — severely incomplete:**
- README.md says "PostgreSQL" but project uses MariaDB
- BACKLOG.md has 2 items (should have 200+)
- No SETUP.md, TESTING.md, DEPLOYMENT.md, CONTRIBUTING.md, LICENSE
- roadmap.md completion status doesn't match reality
- No `.env.example` — secrets hardcoded in source files

**Issues found (full count):**
- Skin: 47+ PHP issues, 13+ JS TODOs, 15+ CSS HACKs, 14 missing Hebrew translations
- CDK: 7 critical security issues, 20+ best practice violations, 0 alarms/monitoring
- Data pipeline: exposed API key, broken team matching, **missing "last mile"** (no code imports data into wiki)
- Docker: 6 critical issues, 10+ high-priority issues
- Docs: 9+ missing critical files

**Cost — current architecture is overkill:**
- Current CDK architecture (ECS Fargate + RDS + ALB + NAT Gateway + WAF): **~$107-128/month**
- Top cost drivers: NAT Gateway ($34-37), Fargate ($20-25), ALB ($18-22), RDS ($17-20)
- For a personal project with ~100-1000 pageviews/day, this can run for **~$16-20/month**

**Data pipeline — half-built:**
- Scrapy spiders scrape Transfermarkt and normalize data to JSONL files
- But there is **zero "last mile" code** — no mwclient, no pywikibot, no API integration
- The data just sits as files. Nothing creates wiki pages from it.
- Scrapy is overkill for a single team (1,800 lines of framework vs. ~180 lines of simple Python)
- `docker-compose.yml` in `data/` references a non-existent `transfermarkt-api/` directory

---

## Cost Analysis & Architecture Decision

*This is a personal project. It should be cheap but scalable if it grows.*

### Current vs. Optimized Cost

| Architecture | Monthly | Notes |
|-------------|---------|-------|
| **Current CDK** (Fargate+RDS+ALB+NAT+WAF) | ~$107-128 | Enterprise-grade, overkill |
| **Quick wins** (remove NAT, use CF free plan) | ~$55-75 | Same architecture, less waste |
| **Cost-conscious** (EC2+RDS, no NAT/ALB) | ~$35-50 | Managed DB, good middle ground |
| **Minimal** (EC2+local MariaDB, CF free) | ~$16-20 | Cheapest viable production setup |

### Biggest Savings (by component)

| Component | Current Cost | Optimization | Savings |
|-----------|-------------|-------------|---------|
| **NAT Gateway** | $34-37/mo | Eliminate — move to public subnet | **$34-37** |
| **ALB** | $18-22/mo | Eliminate — CloudFront direct to EC2/Fargate (VPC origins) | **$18-22** |
| **WAF** | $14-16/mo | Use CloudFront flat-rate free plan (includes WAF with 5 rules) | **$14-16** |
| **ECS Fargate** | $20-25/mo | Replace with t4g.small EC2 ($14/mo, more resources) | **$7-12** |
| **RDS** | $17-20/mo | Run MariaDB on same EC2 (with automated S3 backups) | **$17-20** |
| **Route 53** | $0.50/mo | Included in CloudFront flat-rate free plan | **$0.50** |

### Recommended Architecture: "Cheap but Scalable"

**Phase 1 target: ~$16-20/month**
```
CloudFront (free plan: CDN + WAF 5 rules + Route 53)
    ↓
t4g.small EC2 (2 vCPU, 2 GB RAM — $14/mo)
    ├── MediaWiki + PHP-FPM + Nginx
    ├── MariaDB (local, backed up to S3 daily)
    └── 30 GB gp3 EBS ($2.70/mo)
    ↓
S3 bucket (media uploads, ~$0.15/mo)
```

**If traffic grows (>1000 pageviews/day), scale to ~$35-50/month:**
- Move MariaDB to RDS db.t4g.micro (automated backups, point-in-time recovery)
- Add CloudWatch alarms
- Keep single EC2 — MediaWiki handles thousands of pageviews on 2 GB RAM

**If traffic grows more (>10K/day), scale to ~$80-120/month:**
- Add ALB + second EC2 instance
- Upgrade RDS instance size
- Add auto-scaling

### CDK Plan Changes

The CDK stacks need to be rewritten for the cost-conscious architecture:
- [ ] **Remove**: NAT Gateway, ALB, WAF stack (replaced by CloudFront free plan)
- [ ] **Simplify**: NetworkStack to public subnet only
- [ ] **Replace**: ECS Fargate with EC2 Auto Scaling Group (min: 1, max: 2)
- [ ] **Keep**: CloudFront, S3, Route 53, ACM Certificate
- [ ] **Make optional**: RDS (can toggle between local MariaDB and RDS via config)
- [ ] **Add**: Automated backup Lambda (mysqldump → S3) for when using local MariaDB
- [ ] **Add**: S3 VPC Gateway Endpoint (free, reduces data transfer costs)
- [ ] **Add**: CloudFront flat-rate free plan configuration
- [ ] **Add**: Cost tags and AWS Budget alarm ($25/mo threshold)

---

## Phase 1: Security & Secrets (Do First)

*Goal: Eliminate all credentials from source control and fix critical security vulnerabilities.*

### 1.1 Remove Hardcoded Secrets
- [ ] Create `.env.example` with placeholder values for all secrets
- [ ] Create `.env` (gitignored) with actual values
- [ ] **docker-compose.yml**: Replace hardcoded `MEDIAWIKI_DB_PASSWORD=secret`, `MYSQL_PASSWORD=secret`, `MYSQL_ROOT_PASSWORD=rootpass` with `${VARS}`
- [ ] **LocalSettings.php**: Replace hardcoded `wgSecretKey` and `wgUpgradeKey` with `getenv()` calls
- [ ] **data/tmk-scraper/settings.py**: Move `SCRAPERAPI_KEY` to environment variable
- [ ] Add `.env` to `.gitignore`
- [ ] Document in README that `.env` must be created from `.env.example`

### 1.2 Fix Critical Application Security
- [ ] **XSS in searchResults.js**: `highlightTitle()` doesn't escape HTML — add DOMPurify or manual escaping
- [ ] **HTML injection in PageHeading**: Escape `$editCountHref`, `$msgEditCount` before interpolation
- [ ] **Fragile HTML manipulation in UserInfo**: Replace `str_replace` on rendered HTML with proper DOM
- [ ] **Icon class injection in SkinHooks**: Validate icon names against whitelist
- [ ] **Unvalidated URLs in ApiWebappManifest**: Validate icon src, sizes, MIME types
- [ ] **Citizen v3.9.0 stored XSS fix**: Apply this upstream security patch immediately

### 1.3 Fix Critical Infrastructure Security
- [ ] **CloudFront→ALB**: Change from `HTTP_ONLY` to `HTTPS_ONLY` (`cloudfront-stack.ts:28`)
- [ ] **S3 public access**: Set `blockPublicAccess` to all true (`application-stack.ts:57-62`)
- [ ] **Fargate public IPs**: Set `assignPublicIp: false` (`application-stack.ts:231`)
- [ ] **S3 CORS**: Restrict `allowedHeaders` from `['*']` to specific headers
- [ ] **Security group egress**: Restrict from `allowAllOutbound: true` to specific ports
- [ ] **RDS deletion protection**: Set `deletionProtection: true`, change `removalPolicy` to `SNAPSHOT`
- [ ] **WAF log retention**: Change from 7 days to 90 days (`wiki7-waf-stack.ts:248`)
- [ ] **CDK v1 dependencies**: Remove all `@aws-cdk/*` v1 packages, use only `aws-cdk-lib` v2

### 1.4 Fix Docker Security
- [ ] Pin Dockerfile base image to `mediawiki:1.43.1` (not floating `1.43`)
- [ ] Add `.htaccess` security headers (HSTS, X-Frame-Options, X-Content-Type-Options, CSP)
- [ ] Add HTTPS redirect rule to `.htaccess`
- [ ] Disable/restrict Adminer in production (database UI exposed on port 8081)
- [ ] Add `$wgCookieHttpOnly = true` and `$wgCookieSameSite = 'Lax'` to LocalSettings.php
- [ ] Configure upload restrictions: `$wgMaxUploadSize`, `$wgFileBlacklist`
- [ ] Add rate limiting: `$wgRateLimits` configuration
- [ ] Fix cache directory from `/tmp` (world-readable) to `/var/www/html/cache`

---

## Phase 2: Documentation & Local Development

*Goal: Anyone can clone the repo, run the wiki locally, and understand the whole project.*

### 2.1 Local Development Setup Guide
Create `docs/SETUP.md`:
- [ ] Prerequisites: Docker, Docker Compose, Git, Node.js, Python 3.12 (with versions)
- [ ] Clone instructions including `git submodule update --init --recursive`
- [ ] `.env` setup from `.env.example`
- [ ] `docker compose up` → visit `http://localhost:8080` → verify wiki loads
- [ ] Database access via Adminer at `http://localhost:8081`
- [ ] Data pipeline setup: Poetry install, spider execution order
- [ ] CDK setup: npm install, cdk synth
- [ ] How to stop, restart, reset the environment
- [ ] Troubleshooting: port conflicts, volume permissions, submodule issues

### 2.2 Skin Development Guide
Create `docs/SKIN-DEVELOPMENT.md`:
- [ ] Directory structure (`includes/`, `resources/`, `templates/`, `i18n/`, `skinStyles/`)
- [ ] Template hierarchy diagram (skin.mustache → Header → Drawer → Menu → etc.)
- [ ] How to modify PHP components, templates, LESS styles, JS modules
- [ ] LESS compilation and ResourceLoader module system
- [ ] i18n: how to add/modify Hebrew translations
- [ ] What was customized from upstream Citizen v3.1.0 vs. what was inherited

### 2.3 Data Pipeline Guide
Create `data/README.md`:
- [ ] Purpose: scraping Transfermarkt for Hapoel Beer Sheva data
- [ ] Spider dependency chain: squad → player → fixtures → match
- [ ] Data pipeline flow: scrape → normalize → Hebrew mapping → wiki import
- [ ] How to run each spider and pipeline step
- [ ] Output files and their schemas
- [ ] ScraperAPI configuration and rate limiting

### 2.4 Infrastructure Guide
Create `docs/INFRASTRUCTURE.md`:
- [ ] AWS architecture overview (VPC, ECS, RDS, CloudFront, WAF, S3)
- [ ] CDK stack structure and dependencies
- [ ] How to deploy: `cdk deploy --all`
- [ ] Environment-specific configuration (dev vs. production)
- [ ] Cost estimates and optimization notes

### 2.5 Fix Existing Documentation
- [ ] **README.md**: Fix PostgreSQL→MariaDB error, add project structure, quick-start, links to all docs
- [ ] **BACKLOG.md**: Expand from 2 items to comprehensive backlog from this audit
- [ ] **docs/architecture.md**: Fix DB inconsistency, add Docker/local architecture, add skin architecture
- [ ] **docs/roadmap.md**: Update completion status to match reality
- [ ] **`.gitignore`**: Add `.env`, `.DS_Store`, `node_modules/`, `*.pyc`, `*.log`, `vendor/`, IDE files
- [ ] **`.gitmodules`**: Remove PageSchemas entry, pin Cargo/PageForms to release branches

### 2.6 Fix Docker Configuration
- [ ] Add health checks to all `docker-compose.yml` services
- [ ] Add `depends_on` with `condition: service_healthy`
- [ ] Add restart policies to all services
- [ ] Add resource limits (memory, CPU)
- [ ] Add logging configuration (rotation)
- [ ] Create `docker-compose.override.yml` for dev-specific config
- [ ] Create `.dockerignore`
- [ ] Fix extension submodules — they are currently empty/uninitialized

### 2.7 Create Missing Project Files
- [ ] `CONTRIBUTING.md` — coding standards, branch strategy, PR process
- [ ] `LICENSE` — determine and add license (GPL v2 for MediaWiki compatibility?)
- [ ] `Makefile` — common tasks: `make setup`, `make test`, `make lint`, `make docker-up`
- [ ] `docs/CHANGELOG.md` — document Citizen v3.1.0 customizations, track all changes
- [ ] `.github/ISSUE_TEMPLATE/` — bug report, feature request templates
- [ ] `.github/PULL_REQUEST_TEMPLATE.md`

---

## Phase 3: Testing Infrastructure (TDD Foundation)

*Goal: Full testing pyramid across all components. All subsequent phases use TDD.*

### 3.1 Wiki7 Skin — PHP Tests
**Setup:**
- [ ] PHPUnit configuration in `docker/skins/Wiki7/tests/phpunit/`
- [ ] Test bootstrap integrating with MediaWiki test framework
- [ ] Docker test runner: `docker compose exec mediawiki php tests/phpunit/phpunit.php`
- [ ] `mediawiki/mediawiki-codesniffer` for PHP linting

**Unit tests for every PHP class (23 classes):**

| Group | Classes | Key Test Areas |
|-------|---------|----------------|
| Core | `SkinWiki7`, `GetConfigTrait` | Template data, feature flags, config access |
| Components | `Footer`, `MainMenu`, `Menu`, `MenuListItem`, `Link`, `KeyboardHint` | Rendering, item counting, HTML output |
| Components | `PageHeading`, `PageSidebar`, `PageFooter`, `PageTools`, `SearchBox` | User taglines, last-modified, tools visibility |
| Components | `SiteStats`, `UserInfo` | NumberFormatter, user menu states, exception handling |
| Partials | `Theme`, `BodyContent`, `Metadata` | Theme switching, DOM manipulation, meta tags |
| Hooks | `SkinHooks`, `ResourceLoaderHooks` | Icon mapping, viewport, sidebar, search config |
| API | `ApiWebappManifest`, `ApiWebappManifestFormatJson` | Manifest generation, MIME types, cache headers |

### 3.2 Wiki7 Skin — JavaScript Tests
**Setup:**
- [ ] QUnit + Karma test runner
- [ ] ESLint with `eslint-config-wikimedia`
- [ ] stylelint for LESS files

**Unit tests for every JS module (30+ files across 5 modules):**

| Module | Files | Key Test Areas |
|--------|-------|----------------|
| `skins.wiki7.scripts` | 16 files | Dropdown, TOC, sticky header, scroll/resize observers, sections, search init |
| `skins.wiki7.search` | 10 files | Typeahead, search clients (REST/Action/SMW), history, results highlighting, XSS prevention |
| `skins.wiki7.preferences` | 3 files | Client preferences, localStorage polyfill, portlet polyfill |
| `skins.wiki7.commandPalette` | 4 files | Command/Search/Recent providers, REST client |
| `skins.wiki7.serviceWorker` | 1 file | Service worker lifecycle |

### 3.3 Wiki7 Skin — Visual & Accessibility Tests
- [ ] **BackstopJS**: Baseline screenshots for homepage, article, search, user menu, sidebar, mobile, RTL Hebrew, light/dark/auto themes
- [ ] **axe-core + Cypress**: Automated WCAG 2.1 AA checks
- [ ] RTL-specific accessibility testing

### 3.4 CDK Infrastructure Tests
**Setup:**
- [ ] Un-comment and rewrite `cdk/test/cdk.test.ts`
- [ ] Use CDK assertions library (`aws-cdk-lib/assertions`)

**Snapshot + assertion tests for every stack:**

| Stack | Key Assertions |
|-------|----------------|
| `NetworkStack` | VPC created, public/private subnets, security group rules, NAT gateway |
| `DatabaseStack` | RDS MariaDB, encryption enabled, deletion protection, backup retention |
| `ApplicationStack` | ECS cluster, Fargate task definition, ALB listeners, S3 bucket encryption, IAM roles |
| `CloudFrontStack` | Distribution, cache policies, security headers, OAC |
| `WAFStack` | WAF rules, geo-blocking countries, managed rule groups, logging |
| `CertificateStack` | ACM certificate, domain validation |
| `DNSStack` | Hosted zone, A/AAAA records |
| `BackupStack` | Backup plan, retention, schedule |
| `CrossRegionSSMSync` | Lambda function, SSM parameter handling |

### 3.5 Data Pipeline Tests
**Setup:**
- [ ] pytest configuration in `data/`
- [ ] pytest-mock for mocking HTTP responses
- [ ] Sample fixtures for each spider

**Tests:**

| Component | Key Tests |
|-----------|-----------|
| `squad_spider.py` | Parse squad page HTML, extract player list |
| `player_spider.py` | Parse player profile, market value history, error handling for missing fields |
| `fixtures_spider.py` | Parse season fixtures, competition detection |
| `match_spider.py` | Parse match report, lineup extraction, **fix broken `resolve_team_key()`**, goal/card/sub parsing, sprite minute estimation |
| `helpers.py` | `parse_countries()`, `parse_birth_date()`, `is_all_hebrew()`, `is_homegrown()`, `is_retired()` |
| `schemas.py` | Pydantic model validation, edge cases |
| `normalize_enrich_players.py` | Normalization logic, missing field handling |
| `apply_hebrew_mapping.py` | YAML mapping application, missing keys |
| `generate_mapping_stub.py` | JSONL parsing, stub generation |

### 3.6 Lambda Function Tests
- [ ] `s3_directories.py`: Directory creation, error handling, CloudFormation response
- [ ] `ssm_sync.py`: Parameter retrieval, cross-region sync, error handling

### 3.7 CI/CD Pipeline
Create `.github/workflows/`:
- [ ] **lint.yml**: PHP_CodeSniffer, ESLint, stylelint, Banana Checker, Python flake8/ruff
- [ ] **test-skin.yml**: PHPUnit + QUnit in Docker
- [ ] **test-cdk.yml**: CDK snapshot tests (`npm test`)
- [ ] **test-data.yml**: pytest for data pipeline
- [ ] **visual-regression.yml**: BackstopJS on PRs
- [ ] **accessibility.yml**: axe-core checks
- [ ] **cdk-diff.yml**: `cdk diff` on infrastructure PRs (show what would change)
- [ ] Pre-commit hooks via Husky

### 3.8 Testing Guide
Create `docs/TESTING.md`:
- [ ] How to run each test type locally (skin, CDK, data pipeline)
- [ ] How to write new tests with examples
- [ ] How to update visual regression baselines
- [ ] CI pipeline explanation
- [ ] Coverage goals

---

## Phase 4: Complete & Fix Everything

*Goal: Fix every known issue across all components. TDD: write failing test first, then fix.*

### 4.1 Skin — PHP Fixes (14 items)
- [ ] `SiteStats`: Add logging for IntlException (silent catch)
- [ ] `PageHeading`: Fix undefined `$msgGender`, add permission checks for user data
- [ ] `PageSidebar`: Use MW 1.43 core implementation (TODO)
- [ ] `PageTools`: Fix ULS disabled (FIXME), move handling to SkinWiki7.php (TODO)
- [ ] `UserInfo`: Fix silent MalformedTitleException — add logging
- [ ] `ApiWebappManifest`: Add logging in catch block, cache logo file size lookups
- [ ] `Menu`: Fix `substr_count` HTML counting — use DOM counting
- [ ] `SkinHooks`: Use `str_ends_with()`/`str_starts_with()` (PHP 8.0+)
- [ ] `Partial.php`: Migrate to `SkinComponentRegistryContext`
- [ ] `BodyContent`: Drop T13555 workaround (MW 1.43)
- [ ] Replace `MediaWikiServices::getInstance()` with DI where feasible

### 4.2 Skin — JavaScript Fixes (22 items)
- [ ] `typeahead.js`: Fix Safari blur hack, ineffective debounce, dataset delete
- [ ] `search.js`: Add i18n for clear button aria-label
- [ ] `searchResults.js`: Bound unbounded regex cache
- [ ] `echo.js`: Use MW 1.43 hook, add MutationObserver disconnect
- [ ] `overflowElements.js`: Fix memory leak (nav click listener), float precision
- [ ] `scrollObserver.js`: Fix ineffective throttle cleanup
- [ ] `tableOfContents.js`: Implement MW 1.43 component, deduplicate array
- [ ] `dropdown.js`: Consolidate `beforeunload` listeners
- [ ] `resizeObserver.js`: Fix global variable collision
- [ ] `sw.js`: Implement actual service worker (currently empty)
- [ ] `share.js`: Distinguish AbortError from real errors
- [ ] `mwActionApi.js`: Fix "avaliable" typo
- [ ] `preferences.js`: Migrate fully to clientprefs on MW 1.43
- [ ] `clientPrefs.polyfill.js`: Namespace storage key
- [ ] `addPortlet.polyfill.js`: Check if MW 1.43 fixes the MW 1.41 bug
- [ ] `CommandProvider.js`: Make MAX_COMMAND_RESULTS configurable
- [ ] `searchAction.js`: Move search actions to config file

### 4.3 Skin — Template & Style Fixes (20 items)
- [ ] Refactor Header__logo HACK, remove Desktop Improvements hack
- [ ] Add `aria-expanded` to all `<details><summary>` elements
- [ ] Add `aria-labels` to icon-only buttons, `aria-live` for search results, `aria-busy` for loading
- [ ] Fix `role="menuitem"` on menu items
- [ ] Fix RTL: `direction: ltr` locks in Footer/Common, add `@noflip` annotations
- [ ] Fix hardcoded TOC width (240px), standardize icon size variable
- [ ] Convert Menu.less to core css-icon mixin, merge Pagetools with header__item
- [ ] Replace CSS icon hacks with SVG animations (Drawer__button, Search__button)
- [ ] Fix Parsoid media styles double-loading, intermittent sections class
- [ ] Clean up vendor prefixes and `!important` usage

### 4.4 Skin — Localization
- [ ] Translate 14 missing Hebrew keys (command palette, search, tagline)
- [ ] Validate qqq.json documentation strings
- [ ] Run Banana Checker

### 4.5 CDK Infrastructure Rewrite (cost-conscious)

**Architecture change — from enterprise to personal project:**
- [ ] Remove NAT Gateway — move compute to public subnet (saves ~$35/mo)
- [ ] Remove ALB — use CloudFront VPC origins or direct-to-EC2 (saves ~$20/mo)
- [ ] Remove separate WAF stack — use CloudFront flat-rate free plan's included WAF (saves ~$15/mo)
- [ ] Replace ECS Fargate with EC2 Auto Scaling Group (t4g.small, min:1 max:2)
- [ ] Make RDS optional — support local MariaDB with S3 backup as default
- [ ] Add S3 VPC Gateway Endpoint (free, eliminates S3 NAT traffic)
- [ ] Add automated backup Lambda (mysqldump → S3, daily cron via EventBridge)
- [ ] Add AWS Budget alarm ($25/mo threshold with SNS notification)

**Keep and fix:**
- [ ] CloudFront distribution — switch to flat-rate free plan
- [ ] S3 bucket — fix public access, restrict CORS headers
- [ ] RDS stack — keep as optional module, fix deletion protection and removal policy
- [ ] Set RDS preferred maintenance and backup windows (if RDS enabled)
- [ ] Fix hardcoded domain — parameterize `wiki7.co.il`
- [ ] Remove deprecated CDK context flags
- [ ] Remove CDK v1 dependencies (critical — v1 is EOL)

**Monitoring (proportional to project scale):**
- [ ] Create SNS topic for alerts (email notification)
- [ ] Add CloudWatch alarms: EC2 CPU >80%, disk >85%, CloudFront error rate >5%
- [ ] Enable CloudFront access logging (free)
- [ ] Add resource tags to all resources
- [ ] Add cost allocation tags for tracking

**Defer until traffic justifies cost:**
- Multi-AZ RDS, RDS Proxy, VPC Flow Logs, CloudTrail, GuardDuty, Security Hub, AWS Config

### 4.6 CDK Lambda Fixes
- [ ] `s3_directories.py`: Add environment validation, specific exception handling, request ID logging
- [ ] `ssm_sync.py`: Add `WithDecryption=True`, region validation, retry logic, increase timeout
- [ ] `run_update_task.py`: Use env var for region, add retry logic, validate task startup

### 4.7 Data Pipeline — Evaluate & Rebuild

**Current state: the pipeline is half-built and over-engineered.**

The data pipeline scrapes Transfermarkt and normalizes player/match data to JSONL files, but:
- There is **zero "last mile" code** — nothing imports data into MediaWiki
- Scrapy is overkill for scraping a single team (~1,800 lines of framework boilerplate)
- `items.py` and `pipelines.py` are empty boilerplate — Scrapy's pipeline features are unused
- `docker-compose.yml` references a non-existent `transfermarkt-api/` directory
- Spider execution order is manual with fragile file-based coupling (no orchestration)

**Decision: simplify or keep Scrapy?**

| Approach | Effort | Lines of Code | When it Makes Sense |
|----------|--------|---------------|---------------------|
| **Keep Scrapy, fix issues** | Low | ~1,800 | If expanding to multiple teams/leagues |
| **Replace with simple scripts** | Medium | ~400 | If staying single-team (recommended for now) |

**Recommended: replace with simple Python scripts + add the missing last mile.**

**Step 1: Rewrite scraping (replace Scrapy)**
- [ ] Create `data/scraper/scrape_squad.py` — requests + BeautifulSoup, ~50 lines
- [ ] Create `data/scraper/scrape_players.py` — reads squad.json, enriches with profile/transfers, ~100 lines
- [ ] Create `data/scraper/scrape_fixtures.py` — ~50 lines
- [ ] Create `data/scraper/scrape_matches.py` — reads fixtures.json, parses match details, ~100 lines
- [ ] Add `tenacity` for retry logic (replaces Scrapy's built-in retries)
- [ ] Add `click` or `argparse` for CLI (team ID, season, output dir as params — not hardcoded)
- [ ] Move ScraperAPI key to environment variable
- [ ] Keep Pydantic schemas for data validation
- [ ] Add proper logging (replace print statements)

**Step 2: Keep and fix normalization pipeline**
- [ ] Fix broken `resolve_team_key()` in match processing
- [ ] Add file existence validation before processing
- [ ] Add specific exception handling (replace bare `except Exception`)
- [ ] Add Pydantic validators: non-empty `id`, jersey range (0-99)
- [ ] Make all paths configurable (currently hardcoded relative paths)

**Step 3: Build the missing "last mile" — MediaWiki import**
- [ ] Create `data/wiki_import/import_players.py` — uses `mwclient` to create/update player pages
- [ ] Create `data/wiki_import/import_matches.py` — creates match report pages
- [ ] Create `data/wiki_import/import_templates.py` — creates/updates Cargo table templates
- [ ] Define wiki page templates (Mustache or Jinja2) for each page type:
  - Player infobox page
  - Season squad table
  - Match report page
  - Transfer history table
- [ ] Create bot account in MediaWiki for automated edits
- [ ] Add `$wgGroupPermissions['bot']['bot'] = true` to LocalSettings.php
- [ ] Handle idempotency: check if page exists and data is unchanged before editing
- [ ] Add dry-run mode to preview what would be created/changed

**Step 4: Orchestration**
- [ ] Create `data/run_pipeline.py` — master script that chains: scrape → normalize → import
- [ ] Add `--dry-run`, `--skip-scrape`, `--season` flags
- [ ] Add simple logging and error summary
- [ ] Create `Makefile` target: `make pipeline`
- [ ] Future: schedule via GitHub Actions cron (weekly) or EventBridge Lambda

**Step 5: Data quality**
- [ ] Add data deduplication for transfers and market values
- [ ] Add Hebrew name validation (flag names that aren't Hebrew)
- [ ] Add `.gitignore` entry for `data/output/`
- [ ] Create sample/fixture data for testing

**Legal note on Transfermarkt:**
Scraping violates Transfermarkt's ToS. This is industry standard for fan wikis (Maccabipedia, Wikipedia football projects all do it), and enforcement risk is low for non-commercial projects. But:
- [ ] Document the risk in `data/README.md`
- [ ] Cache aggressively to minimize requests
- [ ] If the wiki becomes commercial, switch to Football-Data.org API (~$4/month)

### 4.8 MediaWiki Configuration Fixes
- [ ] Configure proper caching (currently CACHE_ACCEL with empty memcached = non-functional)
- [ ] Configure SMTP for email (currently uses system mail — won't work in container)
- [ ] Enable `$wgDBssl` for production connections
- [ ] Add `$wgPingback = false` (currently leaks usage data)
- [ ] Add Content Security Policy header
- [ ] Configure ImageMagick security policy

### 4.9 Backlog & Project Management
- [ ] **Font Selection in Preferences Menu** (from BACKLOG.md)
- [ ] Rewrite BACKLOG.md with all items from this audit, categorized and prioritized

---

## Phase 5: Upgrade Everything

*Goal: Bring all components to latest versions. TDD: write compatibility tests before upgrading.*

### 5.1 Citizen Skin Sync (v3.1.0 → v3.13.0)

**Agent team — parallelize analysis by version range:**

| Agent | Versions | Key Changes |
|-------|----------|-------------|
| Agent 1 | v3.2.0–v3.5.0 | Early bug fixes, improvements |
| Agent 2 | v3.6.0–v3.8.0 | Configurable header position, performance mode |
| Agent 3 | v3.9.0–v3.11.0 | **Stored XSS fix**, Codex icons, Cargo/PageForms styling |
| Agent 4 | v3.12.0–v3.13.0 | MW 1.45 compat, PHP 8.4 support |

For each version: diff against Wiki7, categorize (auto-merge / manual / conflict / skip), write tests, apply incrementally.

### 5.2 Extension Updates

| Extension | Action |
|-----------|--------|
| Cargo | Pin to REL1_43 tag, update submodule, test queries |
| PageForms | Pin to REL1_43 tag, update submodule, test form editing |
| PageSchemas | Clean removal — delete `.gitmodules` entry, remove directory |
| mediawiki-aws-s3 | Pin commit hash in Dockerfile, test S3 uploads |

### 5.3 MediaWiki Upgrade (1.43.1 → 1.45.1)

**Pre-upgrade:**
- [ ] Verify PHP 8.2+ available (MW 1.45 drops 8.1)
- [ ] Review breaking changes: removed `$wgParserEnableLegacyHeadingDOM`, `$wgParserEnableLegacyMediaDOM`, `supportsMwHeading`
- [ ] Audit LocalSettings.php and skin code for deprecated APIs

**Upgrade:**
- [ ] Update Dockerfile base image
- [ ] Update LocalSettings.php
- [ ] Run `php maintenance/update.php`
- [ ] Test all skin components, JS modules, extensions
- [ ] Fix breakage (heading/media DOM changes likely affect BodyContent.php)

**Agent team — parallelize testing:**

| Agent | Area |
|-------|------|
| Agent 1 | Skin PHP against MW 1.45 |
| Agent 2 | JS modules against MW 1.45 ResourceLoader |
| Agent 3 | Extension compatibility |
| Agent 4 | LESS/CSS against MW 1.45 core styles |

### 5.4 MariaDB Upgrade
- [ ] Update docker-compose.yml from 10.5 (EOL) to 11.4+ LTS
- [ ] Test database migrations and character set compatibility
- [ ] Update RDS configuration in CDK to match

### 5.5 CDK & Dependencies Upgrade
- [ ] Update CDK from 2.193.0 to latest 2.x
- [ ] Remove all CDK v1 packages (already done in Phase 1.3, verify clean)
- [ ] Update all npm dependencies
- [ ] Review and update deprecated context flags in `cdk.json`
- [ ] Update Python dependencies (boto3, etc.)

### 5.6 Data Pipeline Dependencies
- [ ] Update Pydantic, requests, BeautifulSoup to latest
- [ ] Add `mwclient` for MediaWiki API integration (the missing last mile)
- [ ] Add `tenacity` for retry logic
- [ ] Verify scraper still works with latest Transfermarkt site structure
- [ ] Remove Scrapy and related packages if rewrite is done
- [ ] Update pyproject.toml with dev dependencies (pytest, ruff, mypy)

### 5.7 Docker & Build Modernization
- [ ] Multi-stage Dockerfile (separate build from runtime)
- [ ] Add Composer lock file for reproducible builds
- [ ] Pin all dependency versions
- [ ] Add database SSL/TLS for production
- [ ] Verify Composer integrity (SHA256 check)

---

## Phase 6: Production Readiness & Polish

*Goal: Everything runs smoothly, is monitored, and is maintainable.*

### 6.1 Performance
- [ ] Audit ResourceLoader module sizes
- [ ] Lazy-load command palette (Vue + Pinia — heavy, only needed on Cmd+K)
- [ ] Optimize MutationObserver in echo.js
- [ ] Implement service worker caching strategy
- [ ] Add `<link rel="preload">` for critical fonts
- [ ] Measure Time to Interactive

### 6.2 Accessibility (WCAG 2.1 AA)
- [ ] Full axe-core audit + manual keyboard testing
- [ ] Screen reader testing in Hebrew (NVDA/VoiceOver)
- [ ] Color contrast in light/dark themes
- [ ] `prefers-reduced-motion` support
- [ ] Skip navigation link

### 6.3 Cross-Browser & RTL
- [ ] Chrome, Firefox, Safari, Edge (latest 2 versions)
- [ ] iOS Safari, Android Chrome
- [ ] All polyfills verified
- [ ] Responsive breakpoints on real devices
- [ ] RTL: test every page type, safe-area-insets, bidirectional content

### 6.4 AWS Production Hardening (cost-appropriate)
- [ ] Add AWS Budget alarm ($25/mo with email alert)
- [ ] Add Cost Anomaly Detection (free)
- [ ] Create runbook for common operational tasks
- [ ] Verify backup restore process works (test mysqldump → restore)
- [ ] Set up automated weekly data pipeline run (GitHub Actions cron or EventBridge)
- [ ] **Defer until justified by traffic:** GuardDuty, Security Hub, secrets rotation, CloudTrail

### 6.5 Final Documentation
- [ ] `docs/DEPLOYMENT.md` — full AWS deployment guide with runbook
- [ ] `docs/SECURITY.md` — vulnerability disclosure, security considerations
- [ ] Update `docs/CHANGELOG.md` with all changes from Phases 1-6
- [ ] Update `docs/roadmap.md` to reflect completed work
- [ ] `docs/TROUBLESHOOTING.md` — common issues and fixes

---

## Execution Strategy

### Phase Dependencies & Parallelization

```
PHASE 1: Security & Secrets (CRITICAL — do immediately)
├── Agent A: Remove hardcoded secrets, create .env
├── Agent B: Fix skin security (XSS, injection)
└── Agent C: Fix CDK security (CloudFront, S3, RDS)

PHASE 2: Documentation (unblocks everything else)
├── Agent D: SETUP.md + Docker config fixes
├── Agent E: Skin dev guide + data pipeline guide
├── Agent F: Fix existing docs + create missing files
└── Agent G: Infrastructure guide + changelog

PHASE 3: Testing Infrastructure (TDD foundation)
├── Team 1: Skin PHP tests (4 agents by class group)
├── Team 2: Skin JS tests (3 agents by module)
├── Agent H: CDK stack tests (all 9 stacks)
├── Agent I: Data pipeline tests (spiders + pipeline)
├── Agent J: Visual regression + accessibility setup
└── Agent K: CI/CD pipeline

PHASE 4: Complete & Fix (test-first for each fix)
├── Agent L: Skin PHP fixes
├── Agent M: Skin JS fixes
├── Agent N: Skin template/style/i18n fixes
├── Agent O: CDK infrastructure fixes + monitoring
├── Agent P: Data pipeline rewrite + MediaWiki import (last mile)
└── Agent Q: MediaWiki configuration fixes

PHASE 5: Upgrades (highest risk — careful sequencing)
├── Week 1: Citizen skin sync (4 agents by version range)
├── Week 2: Extensions + MariaDB + CDK deps (parallel)
└── Week 3: MediaWiki 1.45 (4 agents by test area)

PHASE 6: Production Readiness
├── Agent R: Performance audit
├── Agent S: Accessibility + cross-browser + RTL
├── Agent T: AWS production hardening
└── Agent U: Final documentation
```

### TDD Workflow (Phases 4-6)

For every change:
1. Write a failing test that demonstrates the bug/missing feature
2. Implement the fix
3. Verify the test passes
4. Run full test suite to check for regressions
5. Update visual regression baselines if UI changed
6. Update documentation and changelog

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Secrets already in git history | Critical | Rotate all exposed secrets immediately; consider `git filter-branch` for sensitive history |
| Citizen upstream sync conflicts | High | Diff per-file; maintain customization log |
| MW 1.45 breaks skin | High | Test in Docker branch; keep 1.43 as fallback |
| Extension incompatibility | Medium | Test independently before combining |
| MariaDB migration data loss | High | Full backup; test migration on copy first |
| Transfermarkt site changes break scrapers | Medium | CSS selectors are fragile; add tests with saved HTML fixtures |
| Transfermarkt blocks scraping | Low | Use cache, reduce request frequency, consider Football-Data.org API as fallback |
| CDK deployment breaks production | High | `cdk diff` before deploy; rollback plan |
| AWS costs exceed budget | Medium | CloudFront free plan, EC2 instead of Fargate, Budget alarm at $25/mo |
| PHP 8.2 requirement (MW 1.45) | Medium | Verify Docker image PHP version |
| Hebrew RTL regressions | Medium | Visual regression tests + manual review |

---

## Issue Summary

| Component | Critical | High | Medium | Total |
|-----------|----------|------|--------|-------|
| **Skin (PHP)** | 3 (security) | 14 | 6 | 23 |
| **Skin (JS)** | 1 (XSS) | 22 | 5 | 28 |
| **Skin (CSS/Templates)** | 0 | 15 | 20 | 35 |
| **Skin (i18n)** | 0 | 0 | 14 | 14 |
| **CDK Infrastructure** | 7 | 20+ | 15+ | 42+ |
| **Docker/MediaWiki** | 6 | 10 | 9 | 25 |
| **Data Pipeline** | 1 (missing last mile) | 6 | 10+ | 17+ |
| **Documentation** | 0 | 9 | 5 | 14 |
| **TOTAL** | **20** | **96+** | **84+** | **200+** |

---

## Definition of Done (per Phase)

- [ ] All tests pass (unit, integration, visual, accessibility)
- [ ] No linter errors (PHP_CodeSniffer, ESLint, stylelint, Banana, ruff)
- [ ] Documentation updated
- [ ] Changelog updated
- [ ] Local dev environment works from clean clone
- [ ] Hebrew RTL layout verified
- [ ] No hardcoded secrets in source control
- [ ] Code reviewed
