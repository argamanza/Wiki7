# Plan: Test, Complete & Upgrade the Wiki7 Theme

## Context

**Wiki7** is a custom MediaWiki skin for the Hapoel Beer Sheva fan wiki (wiki7.co.il), cloned from the **Citizen skin v3.1.0** and customized with Hebrew localization, club branding, and custom components. It lives in `docker/skins/Wiki7/`.

### Current State (verified Feb 2026)
- **MediaWiki**: 1.43.1 (latest is **1.45.1**)
- **Wiki7/Citizen skin**: v3.1.0 (latest Citizen is **v3.13.0** — 12 minor versions behind)
- **Extensions**: Cargo (latest 3.8.7), PageForms (latest 6.0.5) — versions unknown, need checking
- **MariaDB**: 10.5 in Docker (outdated, EOL)
- **Tests**: Zero. No PHPUnit, no QUnit, no visual regression, no CI pipeline
- **Documentation**: Severely incomplete — no local dev setup guide, no skin dev guide, no deployment guide
- **Issues found**: 47+ PHP issues, 13+ JS TODOs/FIXMEs, 15+ CSS HACKs, 3 security concerns, 14 missing Hebrew translations

### Tech Stack
- PHP (skin components, hooks, API), Mustache (templates), LESS (styles), JavaScript (interactivity)
- 14 PHP classes, 54 JS files across 5 modules, 36 templates, 72+ style files
- Docker Compose for local dev, AWS CDK for infrastructure

---

## Phase 1: Documentation & Local Development

*Goal: Anyone (including future-you) can clone the repo, run the wiki locally, and understand how everything works.*

### 1.1 Local Development Setup Guide
Create `docs/SETUP.md`:
- [ ] Prerequisites: Docker, Docker Compose, Git (with versions), OS compatibility, RAM/disk
- [ ] Clone instructions (including git submodules for Cargo/PageForms)
- [ ] Create `.env.example` template — move hardcoded secrets out of `docker-compose.yml` and `LocalSettings.php`
- [ ] Step-by-step: `docker compose up` → visit `http://localhost:8080` → verify wiki loads
- [ ] Database access via Adminer at `http://localhost:8081`
- [ ] How to stop, restart, reset the environment
- [ ] Troubleshooting: port conflicts, volume permissions, database connection errors, slow startup

### 1.2 Skin Development Guide
Create `docs/SKIN-DEVELOPMENT.md`:
- [ ] Directory structure explanation (`includes/`, `resources/`, `templates/`, `i18n/`, `skinStyles/`)
- [ ] Template hierarchy diagram (skin.mustache → Header → Drawer → Menu → etc.)
- [ ] How to modify PHP components, templates, styles, JS modules
- [ ] How changes are reflected (which require container restart vs. live reload)
- [ ] LESS compilation and ResourceLoader module system explained
- [ ] i18n: how to add/modify Hebrew translations
- [ ] Relationship to upstream Citizen skin — what was customized vs. inherited

### 1.3 Fix Docker Configuration
- [ ] Pin Dockerfile base image to `mediawiki:1.43.1` (not floating `1.43`)
- [ ] Move secrets to `.env` file (database passwords, wgSecretKey, wgUpgradeKey)
- [ ] Add health checks to `docker-compose.yml` services
- [ ] Add restart policy to mediawiki service
- [ ] Create `.dockerignore`
- [ ] Add `--no-install-recommends` to apt-get in Dockerfile
- [ ] Document why each Dockerfile dependency is needed (git, unzip, imagemagick, composer)

### 1.4 Fix Existing Documentation
- [ ] **README.md**: Add project structure overview, quick-start, link to other docs
- [ ] **BACKLOG.md**: Expand from 2 items to full backlog (informed by this audit)
- [ ] **docs/architecture.md**: Add local dev architecture section, fix PostgreSQL/MySQL inconsistency, add missing operational details
- [ ] **docs/roadmap.md**: Update completion status to match reality, add timelines

### 1.5 Changelog & Customization Log
Create `docs/CHANGELOG.md`:
- [ ] Document what was changed from Citizen v3.1.0 to create Wiki7
- [ ] List every custom component, hook override, and style change
- [ ] Track upstream Citizen changes we haven't incorporated (v3.2.0 → v3.13.0)
- [ ] Ongoing: update with every change made in Phases 2-5

---

## Phase 2: Testing Infrastructure (TDD Foundation)

*Goal: Full testing pyramid before making any code changes. All subsequent phases follow TDD — write tests first, then implement.*

### 2.1 PHP Unit Testing Setup
- [ ] Add PHPUnit configuration (`tests/phpunit/` directory in Wiki7 skin)
- [ ] Add `mediawiki/mediawiki-codesniffer` to composer dev dependencies
- [ ] Configure `TestAutoloadNamespaces` in skin.json
- [ ] Create test bootstrap that integrates with MediaWiki test framework
- [ ] Add Docker test runner: `docker compose exec mediawiki php tests/phpunit/phpunit.php`

### 2.2 PHP Unit Tests (all components, not just FIXME-marked)
Write tests for every PHP class:

**Core:**
- [ ] `SkinWiki7` — template data generation, feature flags, client preferences, theme initialization
- [ ] `GetConfigTrait` — config access with exception handling

**Components (14 classes):**
- [ ] `Wiki7ComponentFooter` — footer rendering with custom messages
- [ ] `Wiki7ComponentMainMenu` — sidebar portlet processing, toolbox removal
- [ ] `Wiki7ComponentMenu` — menu rendering, item counting (including the fragile `substr_count` HTML counting)
- [ ] `Wiki7ComponentMenuListItem` — list item wrapping
- [ ] `Wiki7ComponentLink` — link rendering with icons and access key hints
- [ ] `Wiki7ComponentKeyboardHint` — label/key pair rendering
- [ ] `Wiki7ComponentPageHeading` — page title, user tagline (gender, edit count, registration date), namespace taglines
- [ ] `Wiki7ComponentPageSidebar` — last modified info
- [ ] `Wiki7ComponentPageFooter` — footer info labels
- [ ] `Wiki7ComponentPageTools` — article tools visibility, language options, ULS handling
- [ ] `Wiki7ComponentSearchBox` — search box with keyboard hints
- [ ] `Wiki7ComponentSiteStats` — site statistics with NumberFormatter, IntlException handling
- [ ] `Wiki7ComponentUserInfo` — user menu (registered/temp/anon), edit count, groups, user page link

**Partials:**
- [ ] `Theme` — theme switching, clientprefs mapping (day/night/auto)
- [ ] `BodyContent` — collapsible sections, heading decoration, DOM manipulation
- [ ] `Metadata` — theme color meta tag, webapp manifest link

**Hooks:**
- [ ] `SkinHooks` — all 6 hook implementations (icon mapping, viewport, sidebar, edit section links, search config)
- [ ] `ResourceLoaderHooks` — 4 config callbacks

**API:**
- [ ] `ApiWebappManifest` — manifest generation, logo handling, cache headers
- [ ] `ApiWebappManifestFormatJson` — MIME type formatting

### 2.3 JavaScript Testing Setup
- [ ] Set up QUnit (MediaWiki standard) for JS unit tests
- [ ] Configure Karma test runner (`npm run qunit`)
- [ ] Add ESLint with `eslint-config-wikimedia`
- [ ] Add stylelint with MediaWiki config

### 2.4 JavaScript Unit Tests
Write tests for every JS module:

**Core scripts (`skins.wiki7.scripts/`):**
- [ ] `skin.js` — initialization, service worker registration, deferred tasks
- [ ] `dropdown.js` — keyboard navigation, outside click dismissal, pointer detection
- [ ] `echo.js` — Echo notification icon upgrade, MutationObserver lifecycle
- [ ] `lastModified.js` — relative time formatting with Intl.RelativeTimeFormat
- [ ] `overflowElements.js` — horizontal overflow detection, sticky headers, scroll buttons, nav cleanup
- [ ] `sections.js` — collapsible section toggle, edit link click prevention
- [ ] `stickyHeader.js` — show/hide logic, CSS variable sync
- [ ] `tableOfContents.js` — TOC expand/collapse, keyboard arrow navigation, hash fragment handling, section persistence
- [ ] `search.js` — keyboard shortcuts, clear button, lazy module loading, form field detection
- [ ] `share.js` — Web Share API with clipboard fallback, debounced click
- [ ] `speculationRules.js` — preload hint generation, URL filtering
- [ ] `scrollObserver.js` — scroll direction detection, IntersectionObserver
- [ ] `sectionObserver.js` — viewport section tracking for TOC highlighting
- [ ] `resizeObserver.js` — resize lifecycle (start/during/end)
- [ ] `deferUntilFrame.js` — requestAnimationFrame deferral
- [ ] `setupObservers.js` — master observer orchestration

**Search module (`skins.wiki7.search/`):**
- [ ] `typeahead.js` — suggestion rendering, keyboard nav, IME composition, Safari blur hack
- [ ] `searchClient.js` — client factory (mwActionApi, mwRestApi, smwAskApi)
- [ ] `searchHistory.js` — localStorage persistence, max limit, duplicate removal
- [ ] `searchResults.js` — query highlighting, thumbnail handling, **XSS in highlightTitle()** (security test)
- [ ] `searchQuery.js` — query state management
- [ ] `searchAction.js` — action generation (fulltext, mediasearch, edit)
- [ ] `searchPresults.js` — history/placeholder rendering
- [ ] `fetch.js` — AbortController wrapper, error handling
- [ ] `mwRestApi.js` — REST API client, query processing
- [ ] `mwActionApi.js` — Action API client, redirect merging

**Preferences module (`skins.wiki7.preferences/`):**
- [ ] `clientPreferences.js` — radio/switch controls, feature exclusion, i18n
- [ ] `clientPrefs.polyfill.js` — localStorage-based preference storage
- [ ] `addPortlet.polyfill.js` — portlet creation polyfill (MW 1.41 bug workaround)

**Command palette (`skins.wiki7.commandPalette/`):**
- [ ] `CommandProvider.js` — slash command registry, trigger prefix filtering
- [ ] `SearchProvider.js` — search results provider
- [ ] `RecentItemsProvider.js` — recent pages provider
- [ ] `MwRestSearchClient.js` — command palette search client

### 2.5 Visual Regression Testing
- [ ] Set up **BackstopJS** for screenshot comparison
- [ ] Create baseline screenshots for: homepage, article page, search open, user menu, sidebar, mobile viewport, RTL Hebrew layout
- [ ] Configure test scenarios: light theme, dark theme, auto theme
- [ ] Document how to update baselines after intentional changes

### 2.6 Accessibility Testing
- [ ] Integrate **axe-core** for automated WCAG 2.1 AA checks
- [ ] Test with Cypress + cypress-axe plugin
- [ ] Audit all templates for: missing `aria-expanded`, `aria-labels` on icon-only buttons, keyboard focus management, color contrast
- [ ] RTL-specific accessibility: test screen reader with Hebrew content

### 2.7 CI/CD Pipeline
Create `.github/workflows/`:
- [ ] **lint.yml**: PHP_CodeSniffer (mediawiki ruleset), ESLint, stylelint, Banana Checker (i18n validation)
- [ ] **test-php.yml**: PHPUnit unit and integration tests in Docker
- [ ] **test-js.yml**: QUnit tests via Karma
- [ ] **visual-regression.yml**: BackstopJS on PRs (compare against main branch baselines)
- [ ] **accessibility.yml**: axe-core checks
- [ ] Pre-commit hooks via Husky (lint-staged for PHP, JS, LESS, i18n)

### 2.8 Testing Guide
Create `docs/TESTING.md`:
- [ ] How to run each test type locally
- [ ] How to write new tests (with examples)
- [ ] How to update visual regression baselines
- [ ] CI pipeline explanation
- [ ] Coverage requirements and goals

---

## Phase 3: Complete the Theme (Fix All Issues)

*Goal: Fix every known issue — documented TODOs, undocumented bugs, security concerns, and quality gaps. TDD: write failing test first, then fix.*

### 3.1 Security Fixes (Priority: Critical)
- [ ] **XSS in searchResults.js**: `highlightTitle()` doesn't escape HTML — add proper escaping
- [ ] **HTML injection in PageHeading**: Direct variable interpolation without escaping (`$editCountHref`, `$msgEditCount`)
- [ ] **Fragile HTML manipulation in UserInfo**: `str_replace` on rendered HTML — use proper DOM manipulation
- [ ] **Icon class injection in SkinHooks**: Validate icon names against whitelist before CSS class concatenation
- [ ] **Unvalidated icon URLs in ApiWebappManifest**: Validate icon src, sizes, MIME types
- [ ] Move all hardcoded secrets out of `LocalSettings.php` and `docker-compose.yml` into `.env`

### 3.2 PHP Component Fixes
- [ ] **SiteStats**: Add proper logging for IntlException (currently silent catch with FIXME)
- [ ] **PageHeading**: Fix potential undefined `$msgGender` when gender is 'other'
- [ ] **PageHeading**: Add permission checks for viewing user data (edit count, gender)
- [ ] **PageSidebar**: Use MW 1.43 core implementation (currently has TODO for this)
- [ ] **PageTools**: Fix ULS not triggering (hardcoded to false with FIXME)
- [ ] **PageTools**: Move handling to SkinWiki7.php after component conversion (TODO)
- [ ] **UserInfo**: Fix silent MalformedTitleException catch — add logging
- [ ] **ApiWebappManifest**: Add actual logging in catch block (comment says "log" but doesn't)
- [ ] **ApiWebappManifest**: Cache logo file size lookups (currently makes HTTP requests every time)
- [ ] **Menu**: Fix fragile `substr_count` HTML counting — use proper DOM counting
- [ ] **SkinHooks**: Replace `substr()` with `str_ends_with()`/`str_starts_with()` (PHP 8.0+)
- [ ] **Partial.php**: Migrate to `SkinComponentRegistryContext` (TODO)
- [ ] **BodyContent**: Drop T13555 workaround if deployed on MW 1.43 LTS
- [ ] Replace `MediaWikiServices::getInstance()` calls with dependency injection where feasible

### 3.3 JavaScript Fixes
- [ ] **typeahead.js**: Fix Safari blur timing hack (10ms setTimeout) — find proper solution
- [ ] **typeahead.js**: Fix ineffective `mw.util.debounce()` call (return value not used)
- [ ] **typeahead.js**: Replace `delete` on dataset property with `removeAttribute`
- [ ] **search.js**: Add i18n for clear button aria-label (TODO)
- [ ] **searchAction.js**: Save search actions to separate JSON config file (TODO)
- [ ] **searchResults.js**: Bound the regex/text normalization cache (currently grows unbounded)
- [ ] **echo.js**: Switch to `mw.hook('ext.echo.NotificationBadgeWidget.onInitialize')` (MW 1.39 TODO — we're on 1.43)
- [ ] **echo.js**: Add MutationObserver disconnect cleanup
- [ ] **overflowElements.js**: Fix nav click listener not cleaned up in pause() — memory leak
- [ ] **overflowElements.js**: Add floating-point precision guard for `isRightOverflowing`
- [ ] **scrollObserver.js**: Fix ineffective throttle handler in cleanup
- [ ] **tableOfContents.js**: Implement `Wiki7ComponentTableOfContents` (MW 1.39 TODO — we're on 1.43)
- [ ] **tableOfContents.js**: Deduplicate `expandedSections` array
- [ ] **dropdown.js**: Optimize multiple `beforeunload` listeners — delegate to single handler
- [ ] **resizeObserver.js**: Fix global `window.resizedFinished` variable collision risk
- [ ] **CommandProvider.js**: Make MAX_COMMAND_RESULTS configurable
- [ ] **clientPrefs.polyfill.js**: Namespace storage key to site (collision risk on shared domains)
- [ ] **addPortlet.polyfill.js**: Fix `mw.util.addPortlet` disabled — breaks in MW 1.41 (check if fixed in 1.43)
- [ ] **sw.js**: Implement actual service worker (currently placeholder with empty handlers)
- [ ] **share.js**: Fix generic error logging — distinguish AbortError from real errors
- [ ] **mwActionApi.js**: Fix typo "avaliable" → "available"
- [ ] **preferences.js**: Migrate fully to clientprefs on MW 1.43 (TODO)

### 3.4 Template & Style Fixes
- [ ] **Header__logo.mustache**: Refactor icon HACK to use proper component pattern
- [ ] **SkinWiki7.php**: Remove Desktop Improvements page/site tools hack (T287622)
- [ ] Add `aria-expanded` to all `<details><summary>` elements (search, preferences, user menu, dropdowns)
- [ ] Add `aria-labels` to icon-only buttons (currently icon spans without labels)
- [ ] Add `aria-live` region for dynamic search results
- [ ] Add `aria-busy` for loading states
- [ ] Fix missing `role="menuitem"` on individual menu items
- [ ] Fix `direction: ltr` locks in Footer.less and Common.less that may override Hebrew RTL
- [ ] Add `@noflip` annotations where RTL auto-flip should be prevented
- [ ] Fix TOC width hardcoded to 240px (variables.less) — make responsive or configurable
- [ ] Standardize icon size variable (TODO in variables.less)
- [ ] Remove HSL fallbacks when OKLCH is supported (track browser support)
- [ ] Fix `tokens-wiki7.less` naming convention (TODO)
- [ ] Convert Menu.less icon styles to core css-icon mixin (TODO/FIXME)
- [ ] Merge Pagetools styles with header__item (TODO)
- [ ] Replace CSS icon hacks with SVG animations (multiple TODOs in Drawer__button, Search__button)
- [ ] Fix "Parsoid and Parsoid legacy media styles" double-loading (FIXME in skin.less)
- [ ] Fix intermittent `.wiki7-sections-enabled` class missing (FIXME in Sections.less)
- [ ] Clean up vendor prefixes: `-webkit-mask-image`, `-webkit-backdrop-filter`, `-webkit-details-marker`
- [ ] Address `!important` usage in hacks.less and extension overrides

### 3.5 Localization Completeness
- [ ] Translate 14 missing Hebrew keys (mostly command palette strings):
  - `wiki7-command-palette-command-action-description/label`
  - `wiki7-command-palette-command-ns-description/label`
  - `wiki7-command-palette-heading-related`
  - `wiki7-command-palette-keyhint-enter-open/search`
  - `wiki7-command-palette-type-fulltext-search-description`
  - `wiki7-command-palette-type-menu-item`
  - `wiki7-command-palette-type-special-page`
  - `wiki7-search-poweredby-cirrussearch`
  - `wiki7-tagline`, `wiki7.css`, `wiki7.js`
- [ ] Validate all qqq.json documentation strings match current functionality
- [ ] Run Banana Checker to verify i18n file format

### 3.6 Backlog Items
- [ ] **Font Selection in Preferences Menu** (from BACKLOG.md)
- [ ] Update BACKLOG.md with all newly discovered items from this audit

---

## Phase 4: Upgrade Everything

*Goal: Bring all components to latest versions. TDD throughout — write compatibility tests before upgrading, verify they pass after.*

### 4.1 Citizen Skin Sync (v3.1.0 → v3.13.0)

This is a big task. The upstream Citizen skin has had 12 minor releases with significant improvements.

**Agent Team approach — parallelize analysis by version range:**

| Agent | Version Range | Key Changes to Analyze |
|-------|--------------|----------------------|
| Agent 1 | v3.2.0 – v3.5.0 | Early improvements, bug fixes |
| Agent 2 | v3.6.0 – v3.8.0 | Configurable header position, performance mode |
| Agent 3 | v3.9.0 – v3.11.0 | **Security fix (stored XSS)**, Codex icons, section collapse fixes |
| Agent 4 | v3.12.0 – v3.13.0 | MW 1.45 compat, PHP 8.4 fixes, CJK spacing |

**For each version range:**
- [ ] Diff upstream changes against Wiki7 customizations
- [ ] Categorize changes: (a) auto-merge, (b) needs manual merge, (c) conflicts with Wiki7 customizations, (d) skip (not applicable)
- [ ] Write tests for new functionality before merging
- [ ] Apply changes incrementally, running full test suite after each version

**Critical upstream changes to incorporate:**
- [ ] v3.9.0: **Stored XSS security fix** (PRIORITY)
- [ ] v3.7.0: Updated to Codex icons
- [ ] v3.8.0: Configurable header position, performance mode
- [ ] v3.10.0: HSL color fixes, monospace font improvements
- [ ] v3.11.0: Table icons for Cargo, PageForms button styling, section collapse fixes
- [ ] v3.12.0: MW 1.45 compatibility, PHP 8.4 support
- [ ] v3.13.0: Modernized dismiss button styling

### 4.2 Extension Updates

**Agent Team — one agent per extension:**

| Extension | Current | Latest | Action |
|-----------|---------|--------|--------|
| Cargo | Unknown | 3.8.7 | Update submodule, test Cargo queries |
| PageForms | Unknown | 6.0.5 | Update submodule, test form editing |
| PageSchemas | Removed | - | Verify clean removal |
| mediawiki-aws-s3 | Unknown | Latest | Update git clone in Dockerfile, test S3 uploads |

For each extension:
- [ ] Check current version in submodule
- [ ] Read extension changelog for breaking changes
- [ ] Write integration tests for extension functionality before upgrading
- [ ] Update submodule/clone to latest
- [ ] Run tests, fix any breakage

### 4.3 MediaWiki Upgrade (1.43.1 → 1.45.1)

**This is the highest-risk upgrade. Requires careful planning.**

**Pre-upgrade preparation:**
- [ ] Verify PHP 8.2+ is available (MW 1.45 requires it; MW 1.43 may run on 8.1)
- [ ] Review MW 1.45 breaking changes:
  - Removed `$wgParserEnableLegacyHeadingDOM` — new heading markup always enabled
  - Removed `$wgParserEnableLegacyMediaDOM` — new media markup always enabled
  - Removed `supportsMwHeading` skin option — all skins use new heading markup
  - Dropped PHP 8.1 support
- [ ] Audit `LocalSettings.php` for removed config options
- [ ] Audit skin code for deprecated API calls

**Upgrade steps (on development branch):**
- [ ] Update Dockerfile base image from `mediawiki:1.43.1` to `mediawiki:1.45.1`
- [ ] Update `LocalSettings.php` — remove deprecated options, add new required config
- [ ] Run `php maintenance/update.php` to migrate database
- [ ] Test every skin component against new MW APIs
- [ ] Test all extensions compatibility
- [ ] Fix any breakage (heading DOM changes, media DOM changes likely affect BodyContent.php)

**Agent Team — parallelize testing:**

| Agent | Test Area |
|-------|-----------|
| Agent 1 | Skin PHP components against MW 1.45 API |
| Agent 2 | JS modules against MW 1.45 ResourceLoader changes |
| Agent 3 | Extension compatibility (Cargo, PageForms, AWS S3) |
| Agent 4 | LESS/CSS against MW 1.45 core style changes |

### 4.4 MariaDB Upgrade
- [ ] Update `docker-compose.yml` from MariaDB 10.5 (EOL) to latest LTS (11.4+)
- [ ] Test database migrations
- [ ] Verify character set and collation compatibility
- [ ] Update RDS configuration in CDK stack to match

### 4.5 Docker & Infrastructure Updates
- [ ] Update Dockerfile to multi-stage build (reduce image size, separate build from runtime)
- [ ] Add Composer lock file to repo for reproducible builds
- [ ] Pin all dependency versions
- [ ] Update CDK stacks if AWS service versions changed
- [ ] Add database SSL/TLS configuration for production

---

## Phase 5: Quality & Polish

*Goal: Everything runs smoothly, looks good, and is maintainable.*

### 5.1 Performance Audit
- [ ] Audit ResourceLoader module sizes — identify unnecessarily large bundles
- [ ] Implement lazy loading for command palette (Vue + Pinia is heavy, only load on Cmd+K)
- [ ] Optimize MutationObserver usage in echo.js (subtree watching is expensive)
- [ ] Implement actual service worker caching strategy (currently placeholder)
- [ ] Add `<link rel="preload">` for critical fonts
- [ ] Measure and optimize Time to Interactive for article pages

### 5.2 Accessibility Compliance
- [ ] Run full WCAG 2.1 AA audit with axe-core + manual testing
- [ ] Test all interactive components with keyboard-only navigation
- [ ] Test with screen reader (NVDA/VoiceOver) in Hebrew
- [ ] Verify color contrast in both light and dark themes
- [ ] Ensure `prefers-reduced-motion` is respected everywhere
- [ ] Add skip navigation link

### 5.3 Cross-Browser Testing
- [ ] Test on: Chrome, Firefox, Safari, Edge (latest 2 versions)
- [ ] Test on: iOS Safari, Android Chrome
- [ ] Verify all polyfills work (AbortController, clientPrefs, addPortlet)
- [ ] Test responsive breakpoints on real devices

### 5.4 RTL Completeness
- [ ] Audit all `direction: ltr` locks — ensure they don't break Hebrew layout
- [ ] Test every page type in Hebrew: article, talk, special, user, category
- [ ] Verify safe-area-insets work correctly in RTL
- [ ] Test bidirectional content (Hebrew text with English/Latin mixed in)

### 5.5 Final Documentation
- [ ] Create `docs/DEPLOYMENT.md` — full AWS deployment guide
- [ ] Create `CONTRIBUTING.md` — coding standards, branch strategy, PR process
- [ ] Update `docs/CHANGELOG.md` with all Phase 2-5 changes
- [ ] Create `docs/ARCHITECTURE-SKIN.md` — detailed Wiki7 skin architecture for future maintenance
- [ ] Update `docs/roadmap.md` to reflect completed work

---

## Execution Strategy

### Parallel Agent Teams

```
PHASE 1: Documentation (1 week)
├── Agent A: Setup & skin dev guides
├── Agent B: Fix Docker config & .env
└── Agent C: Fix existing docs, create changelog

PHASE 2: Testing Infrastructure (2 weeks)
├── Team 1: PHP test setup + unit tests (agents per component group)
│   ├── Agent A: Core + Partials tests
│   ├── Agent B: Component tests (Footer → Menu → Link → KeyboardHint)
│   ├── Agent C: Component tests (PageHeading → PageSidebar → PageFooter → PageTools)
│   └── Agent D: Hook + API tests
├── Team 2: JS test setup + unit tests (agents per module)
│   ├── Agent E: Core scripts tests
│   ├── Agent F: Search module tests
│   └── Agent G: Preferences + Command Palette tests
├── Agent H: Visual regression (BackstopJS) setup
├── Agent I: Accessibility testing (axe-core) setup
└── Agent J: CI/CD pipeline

PHASE 3: Complete the Theme (2 weeks)
├── Agent K: Security fixes (critical, do first)
├── Team 3: PHP fixes (agents per component)
├── Team 4: JS fixes (agents per module)
├── Agent L: Template & style fixes
└── Agent M: i18n completeness

PHASE 4: Upgrades (3 weeks)
├── Week 1: Citizen skin sync (4 agents by version range)
├── Week 2: Extensions + MariaDB (parallel agents per extension)
└── Week 3: MediaWiki 1.45 upgrade (4 agents by test area)

PHASE 5: Quality & Polish (1 week)
├── Agent N: Performance audit
├── Agent O: Accessibility audit
├── Agent P: Cross-browser testing
└── Agent Q: Final documentation
```

### TDD Workflow (Phases 3-5)

For every change:
1. Write a failing test that demonstrates the bug/missing feature
2. Implement the fix
3. Verify the test passes
4. Run full test suite to check for regressions
5. Update visual regression baselines if UI changed
6. Update documentation/changelog

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Citizen upstream sync conflicts | High — Wiki7 has heavy customizations | Diff carefully per-file; keep list of all Wiki7 customizations |
| MW 1.45 breaks skin | High — heading/media DOM changes | Test in Docker branch first; keep 1.43 as fallback |
| Extension incompatibility after upgrades | Medium — Cargo queries or forms may break | Test extensions independently before combining |
| MariaDB migration data loss | High | Full backup before upgrade; test migration on copy |
| PHP 8.2 requirement (MW 1.45) | Medium — hosting may not support it | Verify hosting PHP version before committing to upgrade |
| No rollback path | High | Git branches per phase; Docker image tags per version |
| Hebrew RTL regressions | Medium — hard to catch automatically | Visual regression tests include RTL screenshots; manual review |

---

## Definition of Done (per Phase)

- [ ] All tests pass (unit, integration, visual, accessibility)
- [ ] No linter errors (PHP_CodeSniffer, ESLint, stylelint, Banana)
- [ ] Documentation updated
- [ ] Changelog updated
- [ ] Local dev environment works from clean clone
- [ ] Hebrew RTL layout verified
- [ ] Code reviewed
