# Backlog

Categorized list of known issues, improvements, and planned work.

## Skin

- [ ] Font Selection in Preferences Menu
- [ ] Fix Safari typeahead blur hack
- [ ] Fix memory leak in overflowElements.js (nav click listener)
- [ ] Implement actual service worker caching (sw.js is empty)
- [ ] Fix ineffective debounce in typeahead
- [ ] Add i18n for clear button aria-label
- [ ] Bound unbounded regex cache in searchResults.js
- [ ] Fix echo.js — use MW 1.45 hook, add MutationObserver disconnect
- [ ] Fix resizeObserver.js global variable collision
- [ ] Migrate preferences to clientprefs on MW 1.45
- [ ] Add aria-expanded to all details/summary elements
- [ ] Add aria-labels to icon-only buttons
- [ ] Fix RTL direction locks in Footer/Common
- [ ] Fix hardcoded TOC width (240px)
- [ ] Translate 14 missing Hebrew i18n keys

## CDK Infrastructure

- [ ] Rewrite for cost-conscious architecture (~$16-20/mo target)
- [ ] Remove NAT Gateway (saves ~$35/mo)
- [ ] Remove ALB — use CloudFront VPC origins
- [ ] Replace ECS Fargate with EC2 (t4g.small)
- [ ] Make RDS optional (local MariaDB + S3 backup)
- [ ] Add AWS Budget alarm ($25/mo threshold)
- [ ] Add CloudWatch alarms (CPU, disk, error rate)
- [ ] Fix hardcoded domain — parameterize wiki7.co.il
- [ ] Remove deprecated CDK context flags

## Data Pipeline

- [ ] Build missing "last mile" — import data into MediaWiki
- [ ] Consider replacing Scrapy with simple scripts
- [ ] Fix broken resolve_team_key() in match processing
- [ ] Fix docker-compose.yml reference to non-existent transfermarkt-api/
- [ ] Add proper logging (replace print statements)
- [ ] Add data deduplication for transfers and market values

## Docker / MediaWiki

- [ ] Configure SMTP for email (won't work in container with system mail)
- [ ] Configure proper caching (CACHE_ACCEL with empty memcached = non-functional)
- [ ] Add Content Security Policy header
- [ ] Configure ImageMagick security policy
- [ ] Enable $wgDBssl for production

## Upgrades

- [ ] Upgrade Wiki7 skin: sync with Citizen v3.1.0 → v3.13.0
- [x] Upgrade MediaWiki: 1.43.1 → 1.45.1 (codebase prepared)
- [x] Upgrade MariaDB: 10.5 (EOL) → 11.4 LTS
- [x] Upgrade CDK from 2.193.0 to latest 2.x
- [x] Update Python dependencies

## Documentation

- [ ] Create DEPLOYMENT.md with full AWS deployment guide
- [ ] Create SECURITY.md
- [ ] Create TROUBLESHOOTING.md
