# Wiki7 Architecture

This document describes the actual architecture of the Wiki7 project in both local development and production environments.

## Local Development

Docker Compose runs three containers:

1. **MediaWiki (Apache + PHP)** — the wiki application with the Wiki7 skin and extensions
2. **MariaDB 10.5** — database
3. **Adminer** — database admin UI (development only)

```
┌──────────────────────────────────────────────┐
│              Docker Compose                  │
│                                              │
│  ┌──────────────┐    ┌──────────────┐        │
│  │  MediaWiki   │    │   Adminer    │        │
│  │  (Apache)    │    │  :8081       │        │
│  │  :8080       │    └──────┬───────┘        │
│  └──────┬───────┘           │                │
│         │                   │                │
│         ▼                   ▼                │
│  ┌─────────────────────────────────┐         │
│  │         MariaDB 10.5           │         │
│  │         :3306                  │         │
│  └─────────────────────────────────┘         │
└──────────────────────────────────────────────┘
```

Configuration is managed through `.env` files (not AWS Secrets Manager). See `docker/.env.example` for required variables.

## Production (AWS via CDK)

The production environment is defined in CDK stacks under `cdk/`. The current architecture:

```
         ┌─────────────────┐
         │   Route 53      │
         │  wiki7.co.il    │
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │   CloudFront    │
         │   (CDN + SSL)   │
         └───────┬─┬───────┘
                 │ │
          ┌──────┘ └──────┐
          ▼               ▼
  ┌──────────────┐ ┌─────────────────┐
  │   S3 Bucket  │ │      WAF        │
  │ (Media Files)│ └────────┬────────┘
  └──────────────┘          │
                            ▼
                   ┌─────────────────┐
                   │      ALB        │
                   │ (Load Balancer) │
                   └────────┬────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │  ECS Fargate    │
                   │  (MediaWiki     │
                   │   + Apache)     │
                   └────────┬────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │   RDS MariaDB   │
                   └─────────────────┘
```

### AWS Services Used

- **Route 53** — DNS for wiki7.co.il
- **CloudFront** — CDN, SSL termination, caching
- **WAF** — web application firewall (rate limiting, common exploit protection)
- **ALB** — application load balancer routing to ECS
- **ECS Fargate** — runs the MediaWiki container (Apache + PHP)
- **RDS MariaDB** — managed database
- **S3** — media file storage
- **CloudWatch** — logging (alarms not yet configured)

### What Does NOT Exist

- **No CI/CD pipeline** — there is no CodePipeline, CodeBuild, or GitHub Actions. Deployments are manual via `cdk deploy`. GitHub Actions CI/CD is planned.
- **No Secrets Manager** — secrets are in `.env` files
- **No Nginx** — MediaWiki runs on Apache
- **No Multi-AZ** — RDS is single-AZ to reduce cost
- **No ElastiCache** — no caching layer beyond CloudFront
- **No NAT Gateway** currently planned for removal (cost optimization)

## Data Flow

1. **User requests** — User -> CloudFront -> WAF -> ALB -> ECS (MediaWiki/Apache) -> RDS MariaDB
2. **Media requests** — User -> CloudFront -> S3
3. **Deployments** — Manual: build Docker image, push to ECR, run `cdk deploy`

## Security

- Private subnets for RDS
- Security groups with restricted access
- HTTPS via CloudFront (ACM certificate)
- WAF rules for rate limiting and common exploits
- Database credentials in `.env` (migration to Secrets Manager is a backlog item)
- Content Security Policy header not yet configured (backlog item)

## Cost Optimization

The current architecture is more expensive than necessary for a personal project. An optimization plan exists (see `docs/plan.md`) targeting ~$16-20/month by:

- Removing the NAT Gateway (~$35/mo savings)
- Removing the ALB in favor of CloudFront VPC origins
- Replacing ECS Fargate with EC2 (t4g.small)
- Making RDS optional (local MariaDB with S3 backups)
