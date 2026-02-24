# Wiki7 Operations Runbook

Operational procedures for the Wiki7 production environment on AWS.

**Architecture:** CloudFront -> EC2 (t4g.small) -> Local MariaDB, with S3 for media storage.
**Region:** il-central-1 (Israel), with us-east-1 for CloudFront certificate and WAF.
**Domain:** wiki7.co.il

---

## Table of Contents

- [Deploy a New Version](#deploy-a-new-version)
- [Roll Back a Deployment](#roll-back-a-deployment)
- [Check Logs](#check-logs)
- [Restart Services](#restart-services)
- [Restore from Backup](#restore-from-backup)
- [Scale Up for Traffic](#scale-up-for-traffic)
- [Common Troubleshooting](#common-troubleshooting)

---

## Deploy a New Version

### CDK Infrastructure Changes

```bash
cd cdk
npm ci

# Preview changes before deploying
npx cdk diff Wiki7CdkStack

# Deploy (requires AWS credentials configured)
npx cdk deploy Wiki7CdkStack
```

For stacks that depend on us-east-1 resources (certificate, WAF), deploy in order:

```bash
npx cdk deploy Wiki7DnsStack
npx cdk deploy Wiki7CertificateStack
npx cdk deploy Wiki7CdkStack
```

### Application Code Changes (MediaWiki/Skin)

1. **Build the new Docker image locally:**
   ```bash
   cd docker
   docker compose build
   ```

2. **Test locally:**
   ```bash
   docker compose up -d
   # Verify at http://localhost:8080
   ```

3. **Deploy to EC2 via SSM Session Manager:**
   ```bash
   # Connect to the EC2 instance
   aws ssm start-session --target <instance-id> --region il-central-1

   # On the EC2 instance:
   cd /var/www/html

   # Pull latest code changes
   git pull origin main

   # Run MediaWiki database update if needed
   php maintenance/run.php update

   # Restart PHP-FPM and Nginx
   sudo systemctl restart php-fpm
   sudo systemctl restart nginx
   ```

4. **Invalidate CloudFront cache (if needed):**
   ```bash
   aws cloudfront create-invalidation \
     --distribution-id <DISTRIBUTION_ID> \
     --paths "/*" \
     --region us-east-1
   ```

### Verify Deployment

```bash
# Check site is responding
curl -I https://wiki7.co.il

# Check MediaWiki API
curl -s "https://wiki7.co.il/api.php?action=query&meta=siteinfo&format=json" | jq .

# Check CloudFront distribution status
aws cloudfront get-distribution --id <DISTRIBUTION_ID> --query "Distribution.Status"
```

---

## Roll Back a Deployment

### Roll Back CDK Infrastructure

CDK tracks CloudFormation stacks. To roll back:

```bash
# Option 1: Redeploy the previous version from git
git checkout <previous-commit>
cd cdk && npx cdk deploy Wiki7CdkStack

# Option 2: Roll back via CloudFormation console
# Go to AWS Console -> CloudFormation -> Wiki7CdkStack -> Roll back
```

### Roll Back Application Code

```bash
# Connect via SSM
aws ssm start-session --target <instance-id> --region il-central-1

# On the EC2 instance:
cd /var/www/html
git log --oneline -5          # Find the commit to roll back to
git checkout <previous-commit>

# Restart services
sudo systemctl restart php-fpm
sudo systemctl restart nginx
```

### Roll Back Database Changes

If a MediaWiki update script caused issues, restore from the daily S3 backup (see [Restore from Backup](#restore-from-backup)).

---

## Check Logs

### CloudWatch Logs

```bash
# List available log groups
aws logs describe-log-groups --query "logGroups[?contains(logGroupName, 'wiki7')]" --region il-central-1

# Tail recent logs from a log group
aws logs tail /aws/ec2/wiki7 --follow --region il-central-1

# Search logs for errors in the last hour
aws logs filter-log-events \
  --log-group-name /aws/ec2/wiki7 \
  --start-time $(date -d '1 hour ago' +%s000) \
  --filter-pattern "ERROR" \
  --region il-central-1
```

### EC2 Instance Logs (via SSM)

```bash
# Connect to instance
aws ssm start-session --target <instance-id> --region il-central-1

# Nginx access/error logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# PHP-FPM logs
sudo tail -f /var/log/php-fpm/error.log

# MariaDB logs
sudo tail -f /var/log/mariadb/mariadb.log

# MediaWiki debug log (if enabled)
sudo tail -f /tmp/mediawiki-debug.log

# User data / bootstrap log
cat /var/log/user-data.log

# System journal
sudo journalctl -u nginx -f
sudo journalctl -u php-fpm -f
sudo journalctl -u mariadb -f
```

### CloudFront Logs

CloudFront access logs are stored in the `wiki7-cloudfront-logs` S3 bucket (30-day retention):

```bash
# List recent log files
aws s3 ls s3://wiki7-cloudfront-logs/ --recursive | tail -20

# Download a log file for analysis
aws s3 cp s3://wiki7-cloudfront-logs/<log-file-path> .
gunzip <log-file>.gz
```

### WAF Logs

WAF logs (blocked requests only) are in CloudWatch log group `aws-waf-logs-wiki7` in us-east-1:

```bash
aws logs filter-log-events \
  --log-group-name aws-waf-logs-wiki7 \
  --start-time $(date -d '1 hour ago' +%s000) \
  --region us-east-1
```

---

## Restart Services

### Restart via SSM Session Manager

```bash
aws ssm start-session --target <instance-id> --region il-central-1

# Restart individual services
sudo systemctl restart nginx
sudo systemctl restart php-fpm
sudo systemctl restart mariadb

# Restart all wiki services
sudo systemctl restart nginx php-fpm mariadb

# Check service status
sudo systemctl status nginx php-fpm mariadb
```

### Restart via SSM Run Command (No SSH Required)

```bash
# Restart Nginx on all ASG instances
aws ssm send-command \
  --document-name "AWS-RunShellScript" \
  --targets "Key=tag:Project,Values=Wiki7" \
  --parameters 'commands=["systemctl restart nginx php-fpm"]' \
  --region il-central-1
```

### Force Replace EC2 Instance

If the instance is unresponsive, terminate it and let the ASG launch a new one:

```bash
# Find instance ID
aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names wiki7-asg \
  --query "AutoScalingGroups[0].Instances[*].InstanceId" \
  --region il-central-1

# Terminate (ASG will auto-replace)
aws autoscaling terminate-instance-in-auto-scaling-group \
  --instance-id <instance-id> \
  --no-should-decrement-desired-capacity \
  --region il-central-1
```

---

## Restore from Backup

### Daily Database Backups

The backup Lambda runs daily at 01:00 UTC, executing `mysqldump` via SSM Run Command and uploading to S3.

**Backups location:** `s3://wiki7-storage/backups/`
**Retention:** 7 days (auto-expired via S3 lifecycle rule)

### Restore Database from S3

```bash
# Connect to EC2 via SSM
aws ssm start-session --target <instance-id> --region il-central-1

# List available backups
aws s3 ls s3://wiki7-storage/backups/ --recursive

# Download the backup
aws s3 cp s3://wiki7-storage/backups/<date>/wikidb.sql.gz /tmp/

# Stop MediaWiki (prevent writes during restore)
sudo systemctl stop nginx php-fpm

# Restore the database
gunzip /tmp/wikidb.sql.gz
mysql -u root wikidb < /tmp/wikidb.sql

# Restart services
sudo systemctl start php-fpm nginx

# Run MediaWiki update to ensure schema is current
cd /var/www/html
php maintenance/run.php update
```

### Restore Media Files

Media files are stored in the versioned S3 bucket `wiki7-storage`. To restore a deleted or corrupted file:

```bash
# List object versions
aws s3api list-object-versions \
  --bucket wiki7-storage \
  --prefix images/<filename>

# Restore a specific version
aws s3api copy-object \
  --bucket wiki7-storage \
  --copy-source wiki7-storage/images/<filename>?versionId=<version-id> \
  --key images/<filename>
```

---

## Scale Up for Traffic

### Manual Scaling

The Auto Scaling Group is configured with min=1, max=2. To handle a traffic spike:

```bash
# Temporarily increase capacity
aws autoscaling update-auto-scaling-group \
  --auto-scaling-group-name wiki7-asg \
  --desired-capacity 2 \
  --max-size 3 \
  --region il-central-1

# After the spike, scale back down
aws autoscaling update-auto-scaling-group \
  --auto-scaling-group-name wiki7-asg \
  --desired-capacity 1 \
  --max-size 2 \
  --region il-central-1
```

### Automatic Scaling

CPU-based auto-scaling is already configured (target: 70% CPU utilization, 5-minute cooldown). The ASG will automatically scale from 1 to 2 instances when CPU is sustained above 70%.

### Upgrade Instance Size

For sustained higher traffic, upgrade the EC2 instance type:

1. Update `cdk/lib/application-stack.ts`:
   ```typescript
   instanceType: ec2.InstanceType.of(
     ec2.InstanceClass.T4G,
     ec2.InstanceSize.MEDIUM  // was SMALL
   ),
   ```
2. Deploy: `cd cdk && npx cdk deploy Wiki7CdkStack`
3. The rolling update policy will replace the instance with zero downtime.

### Enable CloudFront Caching

If traffic is primarily read-heavy, enable caching for wiki pages:

- The default behavior currently has caching disabled (`CACHING_DISABLED`).
- For high traffic, consider adding a cache policy with short TTL (e.g., 60 seconds) for anonymous users.
- Static assets (`/images/*`, `/assets/*`) already have 7-day caching via the `Wiki7StaticContent` cache policy.

---

## Common Troubleshooting

### Site Returns 502/503

1. Check if the EC2 instance is running:
   ```bash
   aws autoscaling describe-auto-scaling-groups \
     --auto-scaling-group-names wiki7-asg \
     --query "AutoScalingGroups[0].Instances" \
     --region il-central-1
   ```
2. Check Nginx and PHP-FPM status via SSM:
   ```bash
   sudo systemctl status nginx php-fpm
   ```
3. Check the origin DNS record (`origin.wiki7.co.il`) points to the correct EC2 public IP.

### High CPU Usage

1. Check CloudWatch alarm `wiki7-ec2-cpu-high` (threshold: 80%).
2. Connect via SSM and inspect:
   ```bash
   top -bn1 | head -20
   # Look for runaway PHP or MariaDB processes
   ```
3. If caused by traffic, the ASG should auto-scale. If caused by a runaway process, kill it:
   ```bash
   sudo kill <pid>
   ```

### Disk Space Full

1. CloudWatch alarm `wiki7-ec2-disk-high` fires at 85%.
2. Connect via SSM and check:
   ```bash
   df -h
   du -sh /var/log/* | sort -rh | head -10
   ```
3. Clean up old logs:
   ```bash
   sudo journalctl --vacuum-time=3d
   sudo find /var/log -name "*.gz" -mtime +7 -delete
   ```

### Database Connection Errors

1. Check MariaDB is running:
   ```bash
   sudo systemctl status mariadb
   ```
2. Check disk space (MariaDB stops if disk is full).
3. Check the MariaDB error log:
   ```bash
   sudo tail -50 /var/log/mariadb/mariadb.log
   ```
4. Restart MariaDB if needed:
   ```bash
   sudo systemctl restart mariadb
   ```

### CloudFront Returning Stale Content

```bash
# Create a full cache invalidation
aws cloudfront create-invalidation \
  --distribution-id <DISTRIBUTION_ID> \
  --paths "/*"

# Or invalidate specific paths
aws cloudfront create-invalidation \
  --distribution-id <DISTRIBUTION_ID> \
  --paths "/wiki/Main_Page" "/load.php"
```

### Budget Alert Triggered

1. Check the AWS Cost Explorer for the current month's spend.
2. Identify which service is driving costs:
   ```bash
   aws ce get-cost-and-usage \
     --time-period Start=$(date +%Y-%m-01),End=$(date +%Y-%m-%d) \
     --granularity MONTHLY \
     --metrics "BlendedCost" \
     --group-by Type=DIMENSION,Key=SERVICE
   ```
3. Common cost spikes:
   - **Data transfer**: Check CloudFront for unusual traffic.
   - **EC2**: Verify only 1 instance is running (ASG may have scaled up and not down).
   - **S3**: Check for large backup files or unexpected uploads.

### SSL Certificate Renewal

The ACM certificate auto-renews via DNS validation. If renewal fails:

1. Check the certificate status:
   ```bash
   aws acm describe-certificate \
     --certificate-arn <cert-arn> \
     --region us-east-1
   ```
2. Verify the Route 53 CNAME validation records still exist.
3. If records are missing, redeploy the certificate stack:
   ```bash
   cd cdk && npx cdk deploy Wiki7CertificateStack
   ```
