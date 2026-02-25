# Wiki7 Project Roadmap

A structured plan for building the Hapoel Beer Sheva fan wiki on MediaWiki with AWS infrastructure.

---

## Technical Stack

- **MediaWiki 1.45.1** -- content engine
- **Wiki7 skin** -- custom skin based on Citizen v3.1.0
- **MariaDB 11.4** -- database (MySQL-compatible)
- **Docker** -- containerized development and production environments
- **AWS CDK** -- infrastructure as code (TypeScript)
- **EC2 (t4g.small)** -- compute (Nginx + PHP-FPM + local MariaDB)
- **S3** -- media storage and backups
- **CloudFront + WAF** -- CDN, SSL termination, and security
- **Route 53** -- DNS management
- **CloudWatch** -- monitoring and alerting

---

## Project Phases

### Phase 1: Environment Setup -- DONE

- [x] Set up GitHub repository with directory structure (`docker/`, `cdk/`, `data/`, `docs/`)
- [x] Create Docker Compose setup for local MediaWiki development
- [x] Design initial AWS infrastructure diagram
- [x] Manual deployment to validate service configurations

### Phase 2: Documentation & Project Setup -- DONE

- [x] Create comprehensive project plan (plan.md)
- [x] Create docs/SETUP.md local development setup guide
- [x] Create docs/SKIN-DEVELOPMENT.md skin development guide
- [x] Create docs/INFRASTRUCTURE.md AWS infrastructure guide
- [x] Create data/README.md data pipeline guide
- [x] Rewrite README.md with accurate project information
- [x] Create CONTRIBUTING.md, LICENSE, Makefile, CHANGELOG.md
- [x] Fix docs/architecture.md and docs/roadmap.md accuracy

### Phase 3: Security & Configuration Hardening -- DONE

- [x] Remove hardcoded secrets, create .env.example, gitignore .env
- [x] Fix XSS, HTML injection, and input validation vulnerabilities in skin
- [x] Add Content Security Policy, cookie security, security headers
- [x] Add upload security (file type restrictions, MIME verification)
- [x] Pin Docker base image, add multi-stage build
- [x] Add Docker health checks, resource limits, log rotation
- [x] Fix CDK security: S3 public access, EBS encryption, IMDSv2, RDS protection
- [x] Add cross-region SSM sync for certificate and WAF ARN replication
- [x] Configure database SSL, SMTP, and caching support

### Phase 4: Infrastructure Optimization -- DONE

- [x] Replace ECS Fargate + ALB with EC2 t4g.small (saves ~$60/mo)
- [x] Remove NAT Gateway (saves ~$35/mo)
- [x] Parameterize domain name and add CDK context flags
- [x] Create EC2 application stack with ASG and auto-scaling
- [x] Configure CloudFront with direct EC2 origin (no ALB)
- [x] Add S3 origin with Origin Access Control for static assets
- [x] Add CloudFront security headers and www-to-apex redirect
- [x] Create monitoring stack (CloudWatch alarms, SNS alerts, AWS Budget)
- [x] Create backup stack (daily mysqldump to S3 via Lambda)
- [x] Create optional managed RDS database stack
- [x] Optimize architecture from ~$107-128/mo to ~$16-20/mo target

### Phase 5: CI/CD Pipeline -- DONE

- [x] Set up GitHub Actions for CI (PHP lint, JS lint, CDK tests, Python lint)
- [x] Add CDK diff workflow for infrastructure PRs
- [ ] Add automated Docker image build and push to ECR
- [ ] Add automated deployment to EC2 on merge to main

### Phase 6: Production Hardening & Documentation -- DONE

- [x] Add AWS Cost Anomaly Detection (free)
- [x] Verify budget alarm and backup Lambda
- [x] Create operations runbook (docs/RUNBOOK.md)
- [x] Create deployment guide (docs/DEPLOYMENT.md)
- [x] Create security documentation (docs/SECURITY.md)
- [x] Create troubleshooting guide (docs/TROUBLESHOOTING.md)
- [x] Update changelog and roadmap

---

## Future Work

### Content & Launch

The site is live at wiki7.co.il but content is sparse. The data pipeline (Scrapy) exists but lacks the "last mile" to import scraped data into MediaWiki.

- [ ] Build data import pipeline (scraped data into MediaWiki)
- [ ] Create seed content (history, players, seasons, matches)
- [ ] Set up structured media management (categories, galleries)
- [ ] Perform load testing and performance audit

### Skin Improvements

- [ ] Fix skin bugs (memory leaks, Safari hacks, debounce issues)
- [ ] Implement service worker caching (sw.js is currently empty)
- [ ] Improve accessibility (aria-labels, aria-expanded)
- [ ] Complete Hebrew i18n (14 missing keys)
- [ ] Upgrade from Citizen v3.1.0 (currently 12 versions behind at v3.13.0)

### Infrastructure Enhancements

- [ ] Add automated Docker image build and push to ECR (CI/CD Phase 5 remaining)
- [ ] Add automated deployment to EC2 on merge to main
- [ ] Configure memcached for production caching
- [ ] Configure SMTP for email notifications
- [ ] Add CloudFront caching policy for anonymous wiki pages

---

## Immediate Priorities

1. Build data import pipeline (scraped Transfermarkt data into MediaWiki)
2. Create seed content for the wiki (players, seasons, match history)
3. Add automated deployment pipeline (GitHub Actions -> EC2)
4. Fix critical skin bugs (memory leaks, accessibility)
5. Configure SMTP for email and memcached for caching
