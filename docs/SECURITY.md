# Wiki7 Security Documentation

Security considerations, configurations, and policies for the Wiki7 project.

---

## Overview

Wiki7 is a personal fan wiki for Hapoel Beer Sheva FC. The security posture is proportional to the project's scope: it protects against common web vulnerabilities and unauthorized access without enterprise-grade compliance overhead.

---

## Secrets Management

### Local Development (.env)

Secrets are stored in a `.env` file at the repository root. This file is gitignored and never committed to version control.

| Secret | Location | Purpose |
|--------|----------|---------|
| `MEDIAWIKI_DB_PASSWORD` | `.env` | Database password for MediaWiki |
| `MYSQL_PASSWORD` | `.env` | MariaDB user password (must match above) |
| `MYSQL_ROOT_PASSWORD` | `.env` | MariaDB root password |
| `WG_SECRET_KEY` | `.env` | MediaWiki session signing key (64-char hex) |
| `WG_UPGRADE_KEY` | `.env` | MediaWiki web installer access key (16-char hex) |
| `SCRAPERAPI_KEY` | `.env` | ScraperAPI key for data scraper (optional) |

**Generating secrets:**
```bash
# Generate WG_SECRET_KEY (64-char hex)
openssl rand -hex 32

# Generate WG_UPGRADE_KEY (16-char hex)
openssl rand -hex 8

# Generate a strong database password
openssl rand -base64 24
```

### Production (AWS)

In production, secrets are managed through:

| Secret | Storage Method | Notes |
|--------|---------------|-------|
| Database password | EC2 environment variables / SSM Parameter Store | Set in `/etc/environment` on EC2 |
| MediaWiki secret key | EC2 environment variables | `WG_SECRET_KEY` in `/etc/environment` |
| MediaWiki upgrade key | EC2 environment variables | `WG_UPGRADE_KEY` in `/etc/environment` |
| SSL certificate | AWS Certificate Manager (ACM) | Auto-managed, DNS-validated |
| EC2 access | SSM Session Manager | No SSH keys needed for regular access |
| S3 access | EC2 IAM instance role | No static credentials needed |

### SSM Parameter Store

Cross-stack configuration values are stored in SSM Parameter Store (not secrets, but infrastructure references):

| Parameter | Region | Purpose |
|-----------|--------|---------|
| `/wiki7/hostedzone/id` | il-central-1 | Route 53 hosted zone ID |
| `/wiki7/hostedzone/name` | il-central-1 | Route 53 hosted zone name |
| `/wiki7/certificate/arn` | il-central-1 | ACM certificate ARN (synced from us-east-1) |

---

## Security Headers

### CloudFront Response Headers Policy

CloudFront adds the following security headers to all responses (configured in `cdk/lib/cloudfront-stack.ts`):

| Header | Value | Purpose |
|--------|-------|---------|
| `X-Content-Type-Options` | `nosniff` | Prevents MIME-type sniffing |
| `X-Frame-Options` | `DENY` | Prevents clickjacking via iframe embedding |
| `X-XSS-Protection` | `1; mode=block` | Enables browser XSS filter |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | Forces HTTPS for 1 year |

### .htaccess Security Headers

Additional headers are set in `docker/.htaccess` for defense-in-depth:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`

### Content Security Policy

Configured in `docker/LocalSettings.php`:

```php
$wgCSPHeader = [
    'default-src' => ["'self'"],
    'script-src'  => ["'self'", "'unsafe-inline'", "'unsafe-eval'"],
    'style-src'   => ["'self'", "'unsafe-inline'"],
    'img-src'     => ["'self'", "data:", "https://upload.wikimedia.org"],
    'font-src'    => ["'self'", "data:"],
    'object-src'  => ["'none'"],
    'frame-ancestors' => ["'self'"],
];
```

**Note:** `unsafe-inline` and `unsafe-eval` are required for MediaWiki's ResourceLoader to function. This is a known MediaWiki limitation.

---

## Network Security

### Security Groups

| Security Group | Inbound Rules | Purpose |
|----------------|---------------|---------|
| EC2 Security Group | TCP 80 (0.0.0.0/0), TCP 22 (0.0.0.0/0) | HTTP from CloudFront, SSH for maintenance |

**Note:** SSH (port 22) is open to all IPs but requires a key pair for authentication. For stronger lockdown, restrict the SSH CIDR to your IP. SSM Session Manager is the preferred access method and does not require port 22.

### CloudFront Origin Verification

CloudFront sends a custom header `X-Origin-Verify: wiki7-cloudfront-secret` to the EC2 origin. Configure Nginx to reject requests without this header to prevent direct access bypassing CloudFront.

### VPC Configuration

- Public subnets only (no NAT Gateway for cost savings)
- S3 VPC Gateway Endpoint (free, eliminates S3 traffic through the internet)
- EC2 instances require IMDSv2 (Instance Metadata Service v2) to prevent SSRF attacks

---

## WAF (Web Application Firewall)

The WAF Web ACL is deployed in us-east-1 and associated with CloudFront. It includes:

| Rule | Priority | Description |
|------|----------|-------------|
| Geo-blocking | 1 | Blocks traffic from 17 countries |
| AWS Common Rule Set | 2 | Core protections (with MediaWiki exclusions) |
| Known Bad Inputs | 3 | Blocks known malicious patterns |
| SQL Injection | 4 | SQL injection protection |
| Linux Rule Set | 5 | Linux-specific attack patterns |
| PHP Rule Set | 6 | PHP-specific attack patterns |
| Rate Limiting | 7 | 2000 requests per 5 minutes per IP |
| Suspicious Patterns | 8 | Directory traversal, bot user-agents |
| Legitimate Bots | 9 | Allow Googlebot, Bingbot |

**WAF Logging:** Only BLOCK actions are logged to CloudWatch (`aws-waf-logs-wiki7`, 3-month retention).

### MediaWiki-Specific WAF Exclusions

The Common Rule Set excludes three rules that conflict with normal MediaWiki operation:
- `SizeRestrictions_BODY` -- MediaWiki page edits can have large POST bodies
- `SizeRestrictions_QUERYSTRING` -- Search queries can generate long query strings
- `CrossSiteScripting_BODY` -- Triggers false positives on image uploads

---

## Application Security

### MediaWiki Configuration

| Setting | Value | Purpose |
|---------|-------|---------|
| `$wgCookieHttpOnly` | `true` | Prevents JavaScript access to session cookies |
| `$wgCookieSameSite` | `Lax` | Prevents CSRF via cross-site requests |
| `$wgPingback` | `false` | Prevents leaking usage data |
| `$wgShowExceptionDetails` | `false` (prod) | Hides internal error details |
| `$wgDebugToolbar` | `false` (prod) | Disables debug UI |
| `$wgGroupPermissions["*"]["edit"]` | `false` | Prevents anonymous editing |
| `$wgEmailAuthentication` | `true` | Requires email verification |
| `$wgVerifyMimeType` | `true` | Validates uploaded file MIME types |
| `$wgStrictFileExtensions` | `true` | Enforces file extension whitelist |

### Upload Security

- **Allowed extensions:** png, gif, jpg, jpeg, webp, svg, pdf, ogg
- **Blocked extensions:** exe, bat, cmd, com, pif, scr, vbs, js, wsf, shtml, php, phtml, cgi
- **MIME type verification:** Enabled (prevents disguised uploads)
- **ImageMagick limits:** Max 100 megapixels to prevent DoS via crafted images

### Docker Security

- Multi-stage build (builder dependencies not in runtime image)
- Base image pinned to `mediawiki:1.45.1`
- Resource limits on all containers (512 MB for MediaWiki, 512 MB for MariaDB)
- Health checks configured
- Log rotation enabled (10 MB max, 3 files)

---

## Infrastructure Security

### EC2 Instance Security

- **IMDSv2 required:** Prevents SSRF attacks against the instance metadata service
- **EBS encryption:** Enabled (AWS-managed keys)
- **SSM Session Manager:** Preferred access method (no SSH keys to manage)
- **CloudWatch Agent:** Installed for system-level monitoring
- **Auto Scaling Group:** Automatic instance replacement on failure

### S3 Bucket Security

- **Block all public access:** Enabled
- **Encryption:** S3-managed encryption (SSE-S3)
- **Versioning:** Enabled (7-day retention for old versions)
- **CORS:** Restricted to `wiki7.co.il` and `www.wiki7.co.il`
- **CloudFront OAC:** S3 is only accessible via CloudFront Origin Access Control

### Backup Security

- Daily automated backups via Lambda + SSM Run Command
- Backups stored in S3 with server-side encryption
- 7-day retention with automatic expiration
- Lambda has minimal IAM permissions (SSM:SendCommand, S3:PutObject)

---

## What Is Protected

| Asset | Protection | Level |
|-------|-----------|-------|
| Wiki content | WAF + CloudFront + anonymous edit prevention | High |
| User accounts | MediaWiki authentication + cookie security | High |
| Database | Local MariaDB (not publicly accessible) + daily backups | Medium |
| Media uploads | S3 with OAC + file type restrictions | High |
| Admin access | SSM Session Manager (no public SSH keys) | High |
| SSL/TLS | ACM certificate + HSTS | High |
| DDoS | CloudFront + WAF rate limiting | Medium |
| Cost control | Budget alarms + cost anomaly detection | Medium |

## What Is NOT Protected

| Risk | Status | Mitigation |
|------|--------|------------|
| Application-level DoS (slow queries) | Not specifically protected | Monitor CPU/memory via CloudWatch |
| Advanced persistent threats | No IDS/IPS | Not proportional to project risk |
| Database encryption at rest | MariaDB is on unencrypted local disk | EBS volume is encrypted |
| Multi-region failover | Single region (il-central-1) | Acceptable for personal project |
| Secrets rotation | Manual process | Set calendar reminders to rotate |
| Zero-day MediaWiki vulnerabilities | Reactive patching | Subscribe to MediaWiki security mailing list |

---

## Vulnerability Disclosure

If you discover a security vulnerability in Wiki7:

1. **Do NOT open a public GitHub issue.**
2. Email the project maintainer directly with:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
3. Allow reasonable time for a fix before any public disclosure.

For vulnerabilities in upstream software (MediaWiki, Citizen skin, AWS CDK), report to the respective project's security contact.

---

## Security Maintenance Checklist

Periodic tasks to maintain security posture:

### Monthly
- [ ] Review CloudWatch alarms for anomalies
- [ ] Check WAF logs for blocked attack patterns
- [ ] Review AWS Cost Explorer for unexpected charges
- [ ] Verify backup Lambda is running successfully

### Quarterly
- [ ] Update MediaWiki to the latest patch release
- [ ] Update PHP and system packages on EC2
- [ ] Review and rotate secrets (database passwords, MediaWiki keys)
- [ ] Review IAM roles and permissions for least privilege
- [ ] Check SSL certificate expiration (ACM auto-renews, but verify)

### Annually
- [ ] Audit WAF rules for relevance
- [ ] Review security group rules
- [ ] Update Docker base image
- [ ] Review and update this security documentation
