# Changelog

All notable changes to Wiki7 will be documented in this file.

## [Unreleased]

### Security
- Remove hardcoded secrets from source control (database passwords, secret keys, API key)
- Create .env.example with placeholder values, .env is gitignored
- Fix XSS vulnerability in search highlight (searchResults.js)
- Fix HTML injection in PageHeading component
- Add icon class validation in SkinHooks
- Add URL validation in ApiWebappManifest
- Fix CDK: CloudFront to origin changed from HTTP to HTTPS
- Fix CDK: S3 block all public access
- Fix CDK: Fargate no public IP assignment
- Fix CDK: Restrict security group egress rules
- Fix CDK: RDS deletion protection enabled, removal policy set to SNAPSHOT
- Fix CDK: WAF log retention extended to 3 months
- Remove CDK v1 EOL dependencies
- Pin Docker base image to mediawiki:1.43.1
- Add security headers in .htaccess (X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy)
- Add cookie security settings (HttpOnly, SameSite=Lax)
- Disable MediaWiki pingback
- Move ScraperAPI key to environment variable

### Documentation
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

### Fixed
- Docker: Add health checks and proper service dependencies
- Docker: Add resource limits and log rotation
- Docker: Fix .gitmodules — remove PageSchemas, pin extensions to REL1_43
- Docker: Create .dockerignore

## [0.1.0] — 2024 (Initial Development)

### Added
- Initial Wiki7 skin based on Citizen v3.1.0
- AWS CDK infrastructure (VPC, ECS, RDS, CloudFront, WAF, S3, Route 53)
- Docker Compose local development environment
- Transfermarkt data scraping pipeline (Scrapy)
- Data normalization pipeline (Pydantic)
- Hebrew localization
- Custom branding for Hapoel Beer Sheva FC
