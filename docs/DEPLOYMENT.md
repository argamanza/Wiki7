# Wiki7 AWS Deployment Guide

Complete guide for deploying Wiki7 (Hapoel Beer Sheva FC fan wiki) to AWS.

---

## Architecture Overview

```
                     Route 53 (wiki7.co.il)
                            |
                     CloudFront (CDN + SSL)
                       /          \
                 S3 Bucket     EC2 (t4g.small)
              (media files)    |-- Nginx
                               |-- PHP-FPM + MediaWiki
                               |-- MariaDB (local)
                               |-- 30 GB gp3 EBS
                               |
                     Lambda (daily backup -> S3)
```

**Target cost:** ~$16-20/month

| Component | Monthly Cost |
|-----------|-------------|
| EC2 t4g.small | ~$14 |
| EBS 30 GB gp3 | ~$2.70 |
| S3 storage | ~$0.15 |
| CloudFront | ~$1-3 |
| Route 53 | $0.50 |
| **Total** | **~$18-20** |

---

## Prerequisites

### Required Tools

| Tool | Version | Installation |
|------|---------|-------------|
| AWS CLI | v2 | [Install guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) |
| Node.js | 18 LTS or 20 LTS | [nodejs.org](https://nodejs.org/) |
| AWS CDK CLI | Latest | `npm install -g aws-cdk` |
| Git | 2.30+ | [git-scm.com](https://git-scm.com/) |

### AWS Account Setup

1. **Create an AWS account** (if you don't have one).
2. **Configure AWS CLI credentials:**
   ```bash
   aws configure
   # Enter: Access Key ID, Secret Access Key, region (il-central-1), output (json)
   ```
3. **Set your account ID as an environment variable:**
   ```bash
   export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
   ```
4. **Bootstrap CDK** in both required regions:
   ```bash
   npx cdk bootstrap aws://$CDK_DEFAULT_ACCOUNT/il-central-1
   npx cdk bootstrap aws://$CDK_DEFAULT_ACCOUNT/us-east-1
   ```

### Domain Setup

1. **Register a domain** (or use an existing one).
2. The CDK stack creates a Route 53 hosted zone. After deploying the DNS stack, copy the NS records to your domain registrar.

---

## Step-by-Step Deployment

### Step 1: Clone and Install Dependencies

```bash
git clone https://github.com/<org>/Wiki7.git
cd Wiki7
git submodule update --init --recursive

cd cdk
npm ci
```

### Step 2: Configure Context Values

Create or edit `cdk/cdk.context.json` (or pass via `-c` flags):

```bash
# Required
export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)

# Configuration flags
DOMAIN_NAME="wiki7.co.il"
ALERT_EMAIL="your-email@example.com"    # For budget and alarm notifications
KEY_PAIR_NAME="your-ec2-keypair"        # Optional: for SSH access
```

### Step 3: Deploy DNS Stack

```bash
cd cdk
npx cdk deploy Wiki7DnsStack \
  -c domainName=$DOMAIN_NAME
```

**After deployment:**
1. Note the NS records from the stack output.
2. Go to your domain registrar and update the nameservers to the ones provided.
3. Wait for DNS propagation (can take up to 48 hours, usually much faster).

Verify:
```bash
dig NS $DOMAIN_NAME
```

### Step 4: Deploy Certificate Stack

The SSL certificate must be in us-east-1 for CloudFront:

```bash
npx cdk deploy Wiki7CertificateStack \
  -c domainName=$DOMAIN_NAME
```

This creates an ACM certificate validated via DNS (automatic if Route 53 hosted zone is set up). The certificate ARN is synced to il-central-1 via SSM Parameter Store using a Lambda function.

Verify:
```bash
aws acm describe-certificate \
  --certificate-arn $(aws ssm get-parameter --name /wiki7/certificate/arn --region il-central-1 --query Parameter.Value --output text) \
  --region us-east-1 \
  --query "Certificate.Status"
```

### Step 5: Deploy Main Infrastructure Stack

```bash
npx cdk deploy Wiki7CdkStack \
  -c domainName=$DOMAIN_NAME \
  -c alertEmail=$ALERT_EMAIL \
  -c keyPairName=$KEY_PAIR_NAME
```

This deploys:
- VPC with public subnets (no NAT Gateway)
- EC2 Auto Scaling Group (1 instance, t4g.small)
- S3 bucket for media storage
- CloudFront distribution with SSL
- Route 53 DNS records
- Monitoring (CloudWatch alarms, SNS alerts, budget alarm, cost anomaly detection)
- Backup (daily Lambda-triggered mysqldump to S3)

### Step 6: Configure EC2 Instance

After the instance launches, connect via SSM Session Manager:

```bash
# Find instance ID
INSTANCE_ID=$(aws autoscaling describe-auto-scaling-groups \
  --query "AutoScalingGroups[?contains(Tags[?Key=='Project'].Value, 'Wiki7')].Instances[0].InstanceId" \
  --output text --region il-central-1)

# Connect
aws ssm start-session --target $INSTANCE_ID --region il-central-1
```

On the instance:
```bash
# Clone the Wiki7 repository
cd /var/www/html
sudo git clone https://github.com/<org>/Wiki7.git .
sudo git submodule update --init --recursive

# Copy configuration
sudo cp docker/LocalSettings.php /var/www/html/LocalSettings.php

# Set environment variables
sudo tee /etc/environment << 'EOF'
WIKI_ENV=production
MEDIAWIKI_DB_HOST=localhost
MEDIAWIKI_DB_NAME=wikidb
MEDIAWIKI_DB_USER=wikiuser
MEDIAWIKI_DB_PASSWORD=<your-secure-password>
WG_SECRET_KEY=<64-char-hex-string>
WG_UPGRADE_KEY=<16-char-hex-string>
S3_BUCKET_NAME=wiki7-storage
EOF

# Initialize the database
mysql -u root -e "CREATE DATABASE IF NOT EXISTS wikidb;"
mysql -u root -e "CREATE USER IF NOT EXISTS 'wikiuser'@'localhost' IDENTIFIED BY '<your-secure-password>';"
mysql -u root -e "GRANT ALL PRIVILEGES ON wikidb.* TO 'wikiuser'@'localhost';"
mysql -u root -e "FLUSH PRIVILEGES;"

# Run MediaWiki installer/updater
php maintenance/run.php update

# Fix permissions
sudo chown -R www-data:www-data /var/www/html

# Configure Nginx for MediaWiki
# (Copy your nginx.conf to /etc/nginx/conf.d/wiki7.conf)

# Restart services
sudo systemctl restart nginx php-fpm mariadb
```

### Step 7: Set Up Origin DNS Record

CloudFront connects to the EC2 instance via `origin.wiki7.co.il`. Create an A record:

```bash
# Get the EC2 public IP
EC2_IP=$(aws ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --query "Reservations[0].Instances[0].PublicIpAddress" \
  --output text --region il-central-1)

# Create origin DNS record in Route 53
HOSTED_ZONE_ID=$(aws ssm get-parameter --name /wiki7/hostedzone/id --region il-central-1 --query Parameter.Value --output text)

aws route53 change-resource-record-sets \
  --hosted-zone-id $HOSTED_ZONE_ID \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "origin.wiki7.co.il",
        "Type": "A",
        "TTL": 300,
        "ResourceRecords": [{"Value": "'$EC2_IP'"}]
      }
    }]
  }'
```

### Step 8: Confirm SNS Subscription

AWS sends a confirmation email to the alert email address. Check your inbox and click the confirmation link. Without this, you will not receive:
- CloudWatch alarm notifications
- Budget alerts
- Cost anomaly alerts

---

## Post-Deployment Verification Checklist

Run through each item after deployment:

- [ ] **Site loads:** `curl -I https://wiki7.co.il` returns 200
- [ ] **HTTPS works:** Certificate is valid and auto-redirects from HTTP
- [ ] **www redirect:** `curl -I https://www.wiki7.co.il` returns 301 to apex
- [ ] **MediaWiki API:** `curl -s "https://wiki7.co.il/api.php?action=query&meta=siteinfo&format=json"` returns valid JSON
- [ ] **CloudFront distribution:** Status is "Deployed" in AWS Console
- [ ] **EC2 instance:** Running and healthy in ASG
- [ ] **MariaDB:** Running and accessible from MediaWiki
- [ ] **S3 bucket:** `wiki7-storage` exists with `images/` and `assets/` prefixes
- [ ] **CloudWatch alarms:** All alarms are in OK state (not INSUFFICIENT_DATA long-term)
- [ ] **SNS subscription:** Email confirmed for alert notifications
- [ ] **Budget alarm:** Configured at $25/month threshold
- [ ] **Backup Lambda:** Scheduled daily at 01:00 UTC (check EventBridge rules)
- [ ] **Security headers:** Check at https://securityheaders.com/?q=wiki7.co.il
- [ ] **SSL certificate:** Verify at https://www.ssllabs.com/ssltest/analyze.html?d=wiki7.co.il
- [ ] **DNS propagation:** `dig A wiki7.co.il` resolves to CloudFront
- [ ] **Image uploads:** Upload a test image through MediaWiki and verify it appears

---

## Rollback Procedure

### Full Stack Rollback

```bash
# Rollback to a previous git commit
git log --oneline -10
git checkout <previous-commit>

# Redeploy
cd cdk
npx cdk deploy Wiki7CdkStack
```

### CloudFormation Rollback

If a deployment fails mid-way, CloudFormation will automatically roll back. If it gets stuck:

1. Go to AWS Console -> CloudFormation -> Wiki7CdkStack.
2. Click "Roll back stack" or "Continue rollback".
3. If resources are stuck, skip them in the rollback settings.

### Application-Only Rollback

If only MediaWiki code needs rollback (not infrastructure):

```bash
# Connect to EC2 via SSM
aws ssm start-session --target <instance-id> --region il-central-1

# Roll back code
cd /var/www/html
git log --oneline -10
git checkout <previous-commit>
sudo systemctl restart php-fpm nginx
```

### Database Rollback

Restore from the daily S3 backup. See the [Runbook](RUNBOOK.md#restore-from-backup) for detailed steps.

---

## Destroying the Stack

To tear down all resources (use with extreme caution):

```bash
cd cdk

# Preview what will be destroyed
npx cdk diff --all

# Destroy all stacks (will prompt for confirmation)
npx cdk destroy --all
```

**Note:** The following resources have protection and will NOT be automatically deleted:
- S3 bucket `wiki7-storage` (RemovalPolicy: RETAIN)
- RDS database (if enabled): deletion protection and SNAPSHOT on removal

You must manually delete these from the AWS Console if you want a complete teardown.

---

## Updating the Deployment

### Regular Updates

```bash
# Pull latest code
git pull origin main

# Check for infrastructure changes
cd cdk
npx cdk diff Wiki7CdkStack

# Deploy if there are changes
npx cdk deploy Wiki7CdkStack

# Update application code on EC2
aws ssm start-session --target <instance-id> --region il-central-1
# Then: cd /var/www/html && git pull && php maintenance/run.php update
```

### CDK Version Upgrades

```bash
cd cdk
npm update aws-cdk-lib constructs
npx cdk diff --all    # Check for breaking changes
npx cdk deploy --all  # Deploy updates
```
