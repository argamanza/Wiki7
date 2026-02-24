# Wiki7 Project Roadmap

A structured plan for building the Hapoel Beer Sheva fan wiki on MediaWiki with AWS infrastructure.

---

## Technical Stack

- **MediaWiki 1.45.1** — content engine
- **Wiki7 skin** — custom skin based on Citizen v3.1.0
- **MariaDB 11.4** — database (MySQL-compatible)
- **Docker** — containerized development and production environments
- **AWS CDK** — infrastructure as code (TypeScript)
- **ECS Fargate** — container orchestration (planned migration to EC2)
- **RDS MariaDB** — managed database
- **S3** — media storage
- **CloudFront + WAF** — CDN and security
- **Route 53** — DNS management

---

## Project Phases

### Phase 1: Environment Setup — DONE

- [x] Set up GitHub repository with directory structure (`docker/`, `cdk/`, `data/`, `docs/`)
- [x] Create Docker Compose setup for local MediaWiki development
- [x] Design initial AWS infrastructure diagram
- [x] Manual deployment to validate service configurations

### Phase 2: Infrastructure as Code — PARTIAL

CDK stacks exist under `cdk/` but have significant issues that need addressing.

- [x] Build CDK stacks for VPC, ECS, RDS, S3, CloudFront
- [x] Configure VPC with public and private subnets
- [x] Deploy MariaDB using RDS with security groups
- [x] Define ECS task definitions and service for MediaWiki container
- [ ] Fix hardcoded domain (wiki7.co.il not parameterized)
- [ ] Remove deprecated CDK context flags
- [ ] Add CloudWatch alarms (CPU, disk, error rate)
- [ ] Add AWS Budget alarm
- [ ] Optimize architecture for cost (~$16-20/mo target)

### Phase 3: CI/CD Pipeline — NOT STARTED

No CI/CD pipeline exists. There is no CodePipeline, CodeBuild, or GitHub Actions configuration. Deployments are currently manual via `cdk deploy`.

- [ ] Set up GitHub Actions for CI (lint, test)
- [ ] Add automated Docker image build and push to ECR
- [ ] Add automated deployment to ECS on merge to main
- [ ] Add health checks and validation steps

### Phase 4: MediaWiki Customization — PARTIAL

The Wiki7 skin (based on Citizen) is functional but has many issues identified in the audit. Extensions are installed but some configuration is incomplete.

- [x] Install MediaWiki extensions (Cargo, PageForms, VisualEditor, etc.)
- [x] Create Wiki7 skin based on Citizen with Hapoel Beer Sheva theming
- [x] Build RTL-compatible layout
- [ ] Fix skin bugs (memory leaks, Safari hacks, debounce issues)
- [ ] Implement service worker caching (sw.js is currently empty)
- [ ] Improve accessibility (aria-labels, aria-expanded)
- [ ] Complete Hebrew i18n (14 missing keys)
- [ ] Configure proper caching (CACHE_ACCEL with memcached)
- [ ] Configure SMTP for email
- [ ] Add Content Security Policy header

### Phase 5: Content & Launch — IN PROGRESS

The site is live at wiki7.co.il but content is sparse. The data pipeline (Scrapy) exists but lacks the "last mile" to import scraped data into MediaWiki.

- [x] Deploy production site at wiki7.co.il
- [x] Build Transfermarkt data scraper (Scrapy pipeline)
- [ ] Build data import pipeline (scraped data into MediaWiki)
- [ ] Create seed content (history, players, seasons, matches)
- [ ] Set up structured media management (categories, galleries)
- [ ] Perform load testing and performance audit

---

## Immediate Priorities

1. Fix critical skin bugs (memory leaks, accessibility)
2. Optimize AWS costs (remove NAT Gateway, consider EC2 over Fargate)
3. Set up GitHub Actions CI/CD
4. Build data import pipeline
5. Upgrade MariaDB 11.4 (approaching EOL) to 11.4+ LTS
