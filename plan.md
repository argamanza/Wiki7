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
- Data pipeline: exposed API key, broken team matching logic, 6 missing error handlers
- Docker: 6 critical issues, 10+ high-priority issues
- Docs: 9+ missing critical files

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

### 4.5 CDK Infrastructure Fixes (25+ items)
**Reliability:**
- [ ] Enable RDS Multi-AZ (`database-stack.ts:39`)
- [ ] Increase to 2+ ECS tasks with auto-scaling (`application-stack.ts:230`)
- [ ] Add 2 NAT gateways for HA (`network-stack.ts:15`)
- [ ] Add ALB HTTPS listener with certificate
- [ ] Set RDS preferred maintenance and backup windows
- [ ] Extend backup retention to 30-90 days
- [ ] Add cross-region backup replication

**Monitoring (currently zero alarms):**
- [ ] Create SNS topic for alert notifications
- [ ] Add CloudWatch alarms: ECS CPU/memory, RDS CPU/connections/storage, ALB target health, CloudFront error rates, WAF block rates, Lambda errors
- [ ] Enable ALB access logging to S3
- [ ] Enable S3 access logging
- [ ] Enable CloudFront access logging
- [ ] Enable VPC Flow Logs
- [ ] Enable CloudTrail
- [ ] Add CloudWatch dashboard

**Other:**
- [ ] Add resource tags (Environment, Owner, CostCenter) to all resources
- [ ] Fix KMS encryption for log groups
- [ ] Remove deprecated CDK context flags in `cdk.json`
- [ ] Fix hardcoded domain name — parameterize `wiki7.co.il`
- [ ] Add RDS Proxy for connection pooling
- [ ] Add AWS Config rules for compliance monitoring
- [ ] Standardize log retention across all resources (90 days minimum)

### 4.6 CDK Lambda Fixes
- [ ] `s3_directories.py`: Add environment validation, specific exception handling, request ID logging
- [ ] `ssm_sync.py`: Add `WithDecryption=True`, region validation, retry logic, increase timeout
- [ ] `run_update_task.py`: Use env var for region, add retry logic, validate task startup

### 4.7 Data Pipeline Fixes (20+ items)
**Critical:**
- [ ] Fix broken `resolve_team_key()` in `match_spider.py` — references non-existent dict keys
- [ ] Add file existence validation before spider execution (squad.json, fixtures.json dependencies)
- [ ] Add specific exception handling (replace bare `except Exception`)

**Error handling:**
- [ ] Add try-except for all file I/O operations
- [ ] Add JSON parsing error handling in `generate_mapping_stub.py`
- [ ] Add YAML validation in `apply_hebrew_mapping.py`
- [ ] Add fallback/logging for missing fields in normalization
- [ ] Add spider execution failure metrics

**Code quality:**
- [ ] Implement Scrapy Items instead of raw dicts (currently unused boilerplate in `items.py`)
- [ ] Implement Scrapy Pipeline for validation/dedup (currently empty boilerplate in `pipelines.py`)
- [ ] Add Pydantic validators: non-empty `id`, min-length `name_english`, jersey number range (0-99)
- [ ] Fix CSS selectors for position extraction in `player_spider.py`
- [ ] Add type hints to all spider methods
- [ ] Add docstrings to all functions
- [ ] Make team ID (2976) and base URL configurable
- [ ] Fix hardcoded relative paths — use config or environment variables
- [ ] Add data deduplication for transfers and market values
- [ ] Add `.gitignore` entry for `output/` in data directory (currently missing from root gitignore)

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
- [ ] Update Scrapy, Pydantic, and all Python packages to latest
- [ ] Verify scraper still works with latest Transfermarkt site changes
- [ ] Update Docker configuration for data pipeline

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

### 6.4 AWS Production Hardening
- [ ] Enable GuardDuty for threat detection
- [ ] Enable AWS Security Hub
- [ ] Implement secrets rotation (RDS password, 30-90 day cycle)
- [ ] Add cost monitoring (AWS Budgets, anomaly detection)
- [ ] Create runbook for common operational tasks
- [ ] Verify backup restore process works

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
├── Agent P: Data pipeline fixes
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
| Transfermarkt site changes break scrapers | Medium | CSS selectors are fragile; add integration tests with fixtures |
| CDK deployment breaks production | High | `cdk diff` before deploy; rollback plan |
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
| **Data Pipeline** | 3 | 6 | 10+ | 19+ |
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
