# Wiki7 Infrastructure Guide

## Overview

Wiki7 uses **AWS CDK** (Cloud Development Kit) to define and deploy all infrastructure for the wiki7.co.il fan wiki. The primary region is **il-central-1** (Israel), with supporting resources in **us-east-1** (required for CloudFront certificates and WAF).

- **Language:** TypeScript
- **CDK version:** 2.x
- **Domain:** wiki7.co.il
- **Current monthly cost:** ~$107-128/month (see Cost Notes below)

The CDK project lives at `cdk/` in the repository root.

---

## Architecture Diagram

```
                         ┌─────────────┐
                         │   Route 53  │
                         │ wiki7.co.il │
                         └──────┬──────┘
                                │
                         ┌──────▼──────┐
                         │  CloudFront │──── WAF (us-east-1)
                         │ Distribution│     - Geo-blocking
                         │             │     - Rate limiting
                         └──┬───────┬──┘     - AWS Managed Rules
                            │       │        - Bot protection
                    ┌───────▼──┐ ┌──▼──────────┐
                    │   ALB    │ │  S3 Bucket   │
                    │ (HTTP)   │ │ wiki7-storage│
                    └────┬─────┘ │  /images/*   │
                         │       │  /assets/*   │
                 ┌───────▼───────┐└─────────────┘
                 │  ECS Fargate  │
                 │  (512 CPU,    │
                 │   1024 MB)    │
                 │               │
                 │  MediaWiki    │
                 │  Container    │
                 └───────┬───────┘
                         │
                  ┌──────▼──────┐
                  │  RDS MariaDB │
                  │  db.t3.micro │
                  │  (11.4)      │
                  └──────────────┘

         ┌──────────────────────────────────┐
         │          VPC (il-central-1)      │
         │  ┌────────────┐ ┌──────────────┐ │
         │  │  Public     │ │  Private     │ │
         │  │  Subnets    │ │  Subnets     │ │
         │  │  (ALB)      │ │  (ECS, RDS)  │ │
         │  └────────────┘ └──────────────┘ │
         │         NAT Gateway (1x)         │
         └──────────────────────────────────┘

         ┌──────────────────────────────────┐
         │       AWS Backup (il-central-1)  │
         │  Daily at 01:00 UTC, 7-day       │
         │  retention, KMS encrypted         │
         └──────────────────────────────────┘
```

**Request flow:**
1. DNS resolves `wiki7.co.il` via Route 53 to CloudFront
2. CloudFront applies WAF rules, terminates TLS
3. Static media (`/images/*`, `/assets/*`) is served directly from S3 via Origin Access Control
4. Dynamic requests are forwarded to the ALB (HTTP)
5. ALB routes to the ECS Fargate container running MediaWiki
6. MediaWiki queries MariaDB on RDS in the private subnet
7. A `www.` to apex redirect is handled by a CloudFront Function

---

## CDK Stacks

The CDK app is defined in `cdk/bin/wiki7.ts`. It creates 4 top-level stacks:

### Top-Level Stacks (deployed independently)

#### 1. `Wiki7DnsStack` (il-central-1)
**File:** `cdk/lib/wiki7-dns-stack.ts`

Creates the Route 53 hosted zone for `wiki7.co.il` and stores the zone ID and name in SSM Parameter Store for cross-stack references.

**Resources:**
- Route 53 hosted zone
- SSM parameters: `/wiki7/hostedzone/id`, `/wiki7/hostedzone/name`
- Output: NS records (to be copied to domain registrar)

#### 2. `Wiki7CertificateStack` (us-east-1)
**File:** `cdk/lib/wiki7-certificate-stack.ts`

Creates an ACM SSL certificate in us-east-1 (required for CloudFront). Validates via DNS using the Route 53 hosted zone. Uses `CrossRegionSsmSync` to replicate the certificate ARN to il-central-1.

**Resources:**
- ACM Certificate for `wiki7.co.il` + `www.wiki7.co.il`
- SSM parameter: `/wiki7/certificate/arn`
- Cross-region SSM sync Lambda (us-east-1 -> il-central-1)

#### 3. `Wiki7WafStack` (us-east-1)
**File:** `cdk/lib/wiki7-waf-stack.ts`

Creates a WAF Web ACL scoped to CloudFront (must be in us-east-1). Includes:

| Rule | Priority | Description |
|------|----------|-------------|
| `BlockCertainCountries` | 1 | Geo-blocks 17 countries |
| `AWSManagedRulesCommonRuleSet` | 2 | Core rule set (with exclusions for MediaWiki large bodies, XSS in uploads) |
| `AWSManagedRulesKnownBadInputsRuleSet` | 3 | Known bad inputs |
| `AWSManagedRulesSQLiRuleSet` | 4 | SQL injection protection |
| `AWSManagedRulesLinuxRuleSet` | 5 | Linux-specific protections |
| `AWSManagedRulesPHPRuleSet` | 6 | PHP-specific protections |
| `RateLimitPerIP` | 7 | 2000 requests per 5 minutes per IP |
| `BlockSuspiciousMediaWikiPatterns` | 8 | Directory traversal and bot User-Agents |
| `AllowLegitimateBot` | 9 | Whitelist Googlebot and Bingbot |

Also provisions:
- CloudWatch log group (`aws-waf-logs-wiki7`, 3-month retention, only logs BLOCK actions)
- SSM parameter: `/wiki7/waf-webacl/arn`
- Cross-region SSM sync Lambda (us-east-1 -> il-central-1)

#### 4. `Wiki7CdkStack` (il-central-1)
**File:** `cdk/lib/wiki7-cdk-stack.ts`

The main stack that composes all il-central-1 resources. Reads SSM parameters for the hosted zone, certificate, and WAF ARN, then instantiates four nested constructs:

### Nested Constructs (inside Wiki7CdkStack)

#### Network Construct
**File:** `cdk/lib/network-stack.ts`

**Resources:**
- VPC with 2 AZs
- Public subnets (for ALB)
- Private subnets with egress (for ECS and RDS)
- 1 NAT Gateway
- Security groups:
  - `MediaWikiSecurityGroup` -- Allows HTTPS outbound (443) and MariaDB outbound (3306) to database SG
  - `Wiki7DatabaseSecurityGroup` -- Allows MariaDB inbound (3306) from MediaWiki SG

#### Database Construct
**File:** `cdk/lib/database-stack.ts`

**Resources:**
- RDS MariaDB 11.4 instance (`db.t3.micro`)
  - 20 GB allocated, 100 GB max auto-scaling
  - Private subnet, not publicly accessible
  - Encrypted storage, deletion protection enabled
  - 7-day automated backups
  - Database name: `wikidb`, user: `wikiuser`
- Secrets Manager secret for database credentials

#### Application Construct
**File:** `cdk/lib/application-stack.ts`

**Resources:**
- ECS Cluster with Container Insights
- Fargate task definition (512 CPU, 1024 MB memory)
- MediaWiki container (built from `docker/` directory)
- Fargate service (1 desired count, private subnet)
- Application Load Balancer (public subnet, HTTP listener on port 80)
- S3 bucket (`wiki7-storage`) for media files
  - Block all public access, versioned, encrypted
  - CORS configured for `wiki7.co.il` and `www.wiki7.co.il`
  - Lifecycle: expire old versions after 7 days
- Lambda function to initialize S3 directories (`assets/`, `images/`)
- IAM roles for ECS tasks (S3 read/write, Secrets Manager read)
- CloudWatch log group (1-month retention)

**Environment variables passed to the container:**
- `MEDIAWIKI_DB_HOST` -- RDS endpoint
- `MEDIAWIKI_DB_NAME` -- `wikidb`
- `MEDIAWIKI_DB_USER` -- `wikiuser`
- `MEDIAWIKI_DB_PASSWORD` -- From Secrets Manager
- `WIKI_ENV` -- `production`
- `S3_BUCKET_NAME` -- S3 bucket name

#### CloudFront Construct
**File:** `cdk/lib/cloudfront-stack.ts`

**Resources:**
- CloudFront distribution with:
  - Default behavior: ALB origin (caching disabled, all methods allowed, all viewer headers forwarded)
  - `images/*` behavior: S3 origin with OAC (7-day default TTL, gzip+brotli compression)
  - `assets/*` behavior: S3 origin with OAC (same caching policy)
  - WAF Web ACL association
  - Security headers policy (X-Content-Type-Options, X-Frame-Options: DENY, XSS-Protection, HSTS 365 days)
- CloudFront Function for `www.` to apex redirect (301)
- Route 53 A records: apex and `www` aliased to CloudFront distribution

#### Backup Construct
**File:** `cdk/lib/backup-stack.ts`

**Resources:**
- AWS Backup vault (`wiki7-backup-vault`) with KMS encryption
- Backup plan: daily at 01:00 UTC, 7-day retention
- Backup selection: RDS database instance

#### Cross-Region SSM Sync
**File:** `cdk/lib/cross-region-ssm-sync.ts`

A reusable construct that syncs SSM Parameter Store values between regions using a Lambda function. Used by both the Certificate and WAF stacks to replicate ARN values from us-east-1 to il-central-1.

**Resources per usage:**
- Lambda function (Python 3.11, `lambda/ssm-sync/ssm_sync.py`)
- IAM role with `ssm:GetParameter` and `ssm:PutParameter` permissions
- Custom resource to invoke the Lambda on create/update

---

## Deployment

### Prerequisites

- AWS CLI configured with credentials
- Node.js and npm installed
- CDK CLI installed (`npm install -g aws-cdk`)
- `CDK_DEFAULT_ACCOUNT` environment variable set to your AWS account ID

### Deploy All Stacks

```bash
cd cdk
npm install
npx cdk deploy --all
```

### Deploy Individual Stacks

Stacks should be deployed in order due to cross-stack dependencies:

```bash
# 1. DNS (creates hosted zone, outputs NS records)
npx cdk deploy Wiki7DnsStack

# 2. Certificate (needs hosted zone for DNS validation)
npx cdk deploy Wiki7CertificateStack

# 3. WAF (independent, but must be before main stack)
npx cdk deploy Wiki7WafStack

# 4. Main stack (needs all SSM parameters from above)
npx cdk deploy Wiki7CdkStack
```

### Useful Commands

```bash
npx cdk diff           # Preview changes before deploying
npx cdk synth          # Synthesize CloudFormation templates
npx cdk destroy --all  # Tear down all stacks (careful!)
npx cdk list           # List all stacks
```

---

## Cost Notes

### Current Architecture Cost (~$107-128/month)

| Component | Monthly Cost | Notes |
|-----------|-------------|-------|
| NAT Gateway | $34-37 | Highest single cost; needed for private subnet egress |
| ECS Fargate | $20-25 | 512 CPU / 1024 MB, always running |
| ALB | $18-22 | Fixed hourly cost + LCU charges |
| RDS db.t3.micro | $17-20 | MariaDB, single-AZ |
| WAF | $14-16 | Web ACL + managed rules |
| CloudFront | $1-3 | Low traffic |
| S3 | < $1 | Media storage |
| Route 53 | $0.50 | Hosted zone |
| Backup / Logs | $1-3 | Backup vault + CloudWatch |

### Planned Optimization (~$16-20/month)

The current architecture is enterprise-grade and overkill for a personal fan wiki. The planned optimization (documented in `plan.md`) replaces ECS Fargate + RDS + ALB + NAT Gateway with a single EC2 instance:

```
CloudFront (free plan with WAF)
    |
t4g.small EC2 ($14/month)
    ├── MediaWiki + PHP-FPM + Nginx
    ├── MariaDB (local, daily S3 backups)
    └── 30 GB gp3 EBS (~$2.70/month)
    |
S3 bucket (media, ~$0.15/month)
```

Key savings: eliminate NAT Gateway ($34), ALB ($18), WAF paid tier ($14), and reduce compute cost by moving from Fargate to EC2.

---

## Configuration

### cdk.json

Located at `cdk/cdk.json`, this file configures the CDK app:

```json
{
  "app": "npx ts-node --prefer-ts-exts bin/wiki7.ts"
}
```

It also contains the standard set of CDK feature flags under `context` that enable modern behaviors (e.g., `@aws-cdk/aws-ec2:restrictDefaultSecurityGroup`, `@aws-cdk/aws-iam:minimizePolicies`).

### SSM Parameters (Cross-Stack Communication)

The stacks communicate through SSM Parameter Store:

| Parameter | Source Stack | Used By |
|-----------|-------------|---------|
| `/wiki7/hostedzone/id` | Wiki7DnsStack | Wiki7CdkStack |
| `/wiki7/hostedzone/name` | Wiki7DnsStack | Wiki7CdkStack |
| `/wiki7/certificate/arn` | Wiki7CertificateStack | Wiki7CdkStack |
| `/wiki7/waf-webacl/arn` | Wiki7WafStack | Wiki7CdkStack |

### Environment Variables

The MediaWiki container receives these at runtime:

| Variable | Source | Description |
|----------|--------|-------------|
| `MEDIAWIKI_DB_HOST` | RDS endpoint | Database hostname |
| `MEDIAWIKI_DB_NAME` | Hardcoded `wikidb` | Database name |
| `MEDIAWIKI_DB_USER` | Hardcoded `wikiuser` | Database username |
| `MEDIAWIKI_DB_PASSWORD` | Secrets Manager | Database password (injected as ECS secret) |
| `WIKI_ENV` | Hardcoded `production` | Environment identifier |
| `S3_BUCKET_NAME` | S3 bucket name | Media storage bucket |

### Lambda Functions

Two Lambda functions support the infrastructure:

| Lambda | Location | Purpose |
|--------|----------|---------|
| S3 Directories | `cdk/lambda/s3-directories/` | Creates `assets/` and `images/` prefixes in S3 on stack creation |
| SSM Sync | `cdk/lambda/ssm-sync/` | Copies SSM parameters from us-east-1 to il-central-1 |

Both are Python 3.11 with 30-second timeouts.
