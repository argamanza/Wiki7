# Changelog

All notable changes to Wiki7 will be documented in this file.

## [Unreleased]

### Phase 6: Production Hardening & Documentation (2026-02-24)

#### Phase 6.4: AWS Production Hardening
- Add AWS Cost Anomaly Detection to monitoring stack (free service, alerts on $5+ anomalies)
- Verify AWS Budget alarm exists ($25/mo threshold with 80%/100% actual and 100% forecasted alerts)
- Verify backup Lambda exists (daily mysqldump to S3 at 01:00 UTC, 7-day retention)
- Create operations runbook (docs/RUNBOOK.md)

#### Phase 6.5: Final Documentation
- Create deployment guide (docs/DEPLOYMENT.md)
- Create security documentation (docs/SECURITY.md)
- Create troubleshooting guide (docs/TROUBLESHOOTING.md)
- Update changelog with all Phase 3-6 changes (docs/CHANGELOG.md)
- Update roadmap marking completed phases (docs/roadmap.md)

### Phase 5: CI/CD & GitHub Actions (2026-02-24)

#### Phase 5.1: GitHub Actions CI
- Add `lint-and-test.yml` workflow: PHP lint (MediaWiki CodeSniffer), JS lint (ESLint), CDK tests (npm test), Python lint (ruff)
- Add `cdk-diff.yml` workflow: runs `cdk synth` and `cdk diff` on PRs that modify `cdk/` files

### Phase 4: Infrastructure Optimization (2026-02-24)

#### Phase 4.1: Cost Optimization
- Replace ECS Fargate + ALB with EC2 t4g.small Auto Scaling Group (~$14/mo vs ~$43/mo)
- Remove NAT Gateway (saves ~$35/mo) — EC2 in public subnet
- Remove separate WAF stack from main deployment (CloudFront provides built-in protection)
- Make RDS optional — default to local MariaDB on EC2 with S3 backups
- Add S3 VPC Gateway Endpoint (free, eliminates S3 NAT traffic costs)
- Reduce target monthly cost from ~$107-128 to ~$16-20

#### Phase 4.2: Parameterization
- Parameterize domain name (no longer hardcoded to wiki7.co.il)
- Add CDK context flags for cost control: `enableRds`, `enableMultiAz`, `enablePrivateSubnets`
- Add `alertEmail`, `keyPairName`, `budgetThresholdUsd` as configurable parameters
- Move from hardcoded us-east-1 region to configurable `primaryRegion` context

#### Phase 4.3: EC2 Application Stack
- Create application-stack.ts with EC2 ASG (min:1, max:2, desired:1)
- Add CPU-based auto-scaling (target 70%, 5-minute cooldown)
- Add S3 bucket for MediaWiki storage (versioned, encrypted, CORS configured)
- Add Lambda for S3 directory initialization (assets/, images/)
- Add IAM role with SSM, CloudWatch Agent, and S3 permissions
- Use Launch Template with IMDSv2 required and encrypted EBS
- Add user data script for Nginx, PHP-FPM, MariaDB, CloudWatch Agent installation

#### Phase 4.4: CloudFront Direct-to-EC2
- Configure CloudFront with direct EC2 origin (eliminates ALB)
- Add S3 origin with Origin Access Control for static assets
- Add CloudFront Function for www-to-apex redirect (301)
- Add security headers response policy (X-Content-Type-Options, X-Frame-Options, XSS-Protection, HSTS)
- Add static content cache policy (7-day default TTL, gzip + brotli compression)
- Add CloudFront access logging to S3 (30-day retention)

#### Phase 4.5: Monitoring & Backup
- Create monitoring-stack.ts with SNS alert topic
- Add CloudWatch alarms: EC2 CPU (>80%), disk usage (>85%), CloudFront 5xx error rate (>5%)
- Add AWS Budget alarm ($25/mo threshold, 80% and 100% actual notifications, 100% forecasted)
- Create backup-stack.ts with Lambda for daily mysqldump via SSM Run Command
- Add EventBridge rule for daily backup at 01:00 UTC
- Add S3 lifecycle rule for 7-day backup retention

#### Phase 4.6: Network Stack
- Create network-stack.ts with VPC (2 AZs, public subnets only by default)
- Optional private subnets with NAT Gateway (controlled by `enablePrivateSubnets` flag)
- Add S3 VPC Gateway Endpoint
- Add EC2 security group (HTTP from CloudFront, SSH for maintenance)

#### Phase 4.7: Optional Database Stack
- Create database-stack.ts as optional managed RDS MariaDB 11.4
- Configurable instance size, Multi-AZ, storage auto-scaling
- Secrets Manager for database credentials
- Deletion protection and SNAPSHOT removal policy

### Phase 3: Security & Configuration Hardening (2026-02-24)

#### Phase 3.1: Secrets Management
- Remove hardcoded secrets from source control (database passwords, secret keys, API key)
- Create .env.example with placeholder values
- Add .env to .gitignore
- Move ScraperAPI key to environment variable

#### Phase 3.2: MediaWiki Security
- Fix XSS vulnerability in search highlight (searchResults.js)
- Fix HTML injection in PageHeading component
- Add icon class validation in SkinHooks
- Add URL validation in ApiWebappManifest
- Add Content Security Policy header configuration
- Add cookie security settings (HttpOnly, SameSite=Lax)
- Disable MediaWiki pingback
- Add security headers in .htaccess (X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy)
- Add upload security (file type restrictions, MIME verification, ImageMagick limits)
- Add environment-specific settings (production vs development mode)

#### Phase 3.3: Docker Hardening
- Pin Docker base image to mediawiki:1.45.1
- Add multi-stage build (builder dependencies not in runtime)
- Add health checks and proper service dependencies
- Add resource limits (512 MB) and log rotation (10 MB, 3 files)
- Fix .gitmodules — remove PageSchemas, pin extensions to REL1_43
- Create .dockerignore

#### Phase 3.4: CDK Security Fixes
- Fix CloudFront to origin: configure HTTP-only origin protocol
- Fix S3: block all public access, add OAC for CloudFront
- Add IMDSv2 requirement on EC2 instances
- Add EBS volume encryption
- Fix RDS: enable deletion protection, set removal policy to SNAPSHOT
- Fix WAF: extend log retention to 3 months, log only BLOCK actions
- Remove CDK v1 EOL dependencies

#### Phase 3.5: Cross-Region Infrastructure
- Create cross-region SSM sync construct for parameter replication
- Set up ACM certificate in us-east-1 with DNS validation
- Set up WAF Web ACL in us-east-1 with comprehensive rules
- Add SSM parameter-based cross-stack communication

#### Phase 3.6: Database Configuration
- Add database SSL support (configurable via environment variable)
- Add SMTP configuration support (configurable via environment variables)
- Add memcached caching support (configurable via environment variable)
- Add environment-specific cache settings (CACHE_NONE for dev, CACHE_DB/CACHE_MEMCACHED for prod)

### Phase 2: Documentation & Project Setup (2026-02-24)

- Create comprehensive project plan (plan.md)
- Create docs/SETUP.md local development setup guide
- Create docs/SKIN-DEVELOPMENT.md skin development guide
- Create docs/INFRASTRUCTURE.md AWS infrastructure guide
- Create data/README.md data pipeline guide
- Rewrite README.md with accurate project information
- Expand BACKLOG.md with full audit results
- Fix docs/architecture.md — correct database type, remove inaccurate claims
- Fix docs/roadmap.md — update completion status to match reality
- Create CONTRIBUTING.md, LICENSE, Makefile, CHANGELOG.md

## [0.1.0] -- 2024 (Initial Development)

### Added
- Initial Wiki7 skin based on Citizen v3.1.0
- AWS CDK infrastructure (VPC, ECS, RDS, CloudFront, WAF, S3, Route 53)
- Docker Compose local development environment
- Transfermarkt data scraping pipeline (Scrapy)
- Data normalization pipeline (Pydantic)
- Hebrew localization
- Custom branding for Hapoel Beer Sheva FC
