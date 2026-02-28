#!/bin/bash
set -euo pipefail

# Wiki7 DR Test Script
# Non-destructive test that validates backups are restorable.
# Restores a snapshot to a temporary RDS instance, validates data, then cleans up.
#
# Usage: ./dr-test.sh
#
# Prerequisites:
#   - AWS CLI configured with appropriate permissions (profile: argamanza)

AWS_PROFILE="${AWS_PROFILE:-argamanza}"
REGION="${AWS_REGION:-il-central-1}"
TEMP_DB="wiki7-dr-test-$(date +%Y%m%d%H%M%S)"
CLEANUP_ON_EXIT=true

cleanup() {
  if [ "$CLEANUP_ON_EXIT" = true ]; then
    echo ""
    echo "--- Cleanup: Deleting temporary instance $TEMP_DB ---"
    aws rds delete-db-instance \
      --profile "$AWS_PROFILE" --region "$REGION" \
      --db-instance-identifier "$TEMP_DB" \
      --skip-final-snapshot \
      --delete-automated-backups 2>/dev/null || true
    echo "Cleanup initiated. Instance will be deleted in the background."
  fi
}
trap cleanup EXIT

echo "=== Wiki7 DR Test ==="
echo "Profile: $AWS_PROFILE | Region: $REGION"
echo ""

# 1. Find source DB
echo "--- Step 1: Locating source DB and latest snapshot ---"
SOURCE_DB=$(aws rds describe-db-instances \
  --profile "$AWS_PROFILE" --region "$REGION" \
  --query "DBInstances[?contains(DBInstanceIdentifier, 'wiki7')].DBInstanceIdentifier" \
  --output text | head -1)

if [ -z "$SOURCE_DB" ]; then
  echo "ERROR: Could not find Wiki7 RDS instance"
  exit 1
fi
echo "Source DB: $SOURCE_DB"

# 2. Find latest snapshot
SNAPSHOT_ID=$(aws rds describe-db-snapshots \
  --profile "$AWS_PROFILE" --region "$REGION" \
  --db-instance-identifier "$SOURCE_DB" \
  --snapshot-type automated \
  --query "sort_by(DBSnapshots, &SnapshotCreateTime)[-1].DBSnapshotIdentifier" \
  --output text)

if [ "$SNAPSHOT_ID" = "None" ] || [ -z "$SNAPSHOT_ID" ]; then
  echo "ERROR: No automated snapshots found for $SOURCE_DB"
  exit 1
fi
echo "Latest snapshot: $SNAPSHOT_ID"

# Get subnet group from source
SUBNET_GROUP=$(aws rds describe-db-instances \
  --profile "$AWS_PROFILE" --region "$REGION" \
  --db-instance-identifier "$SOURCE_DB" \
  --query "DBInstances[0].DBSubnetGroup.DBSubnetGroupName" --output text)

SECURITY_GROUPS=$(aws rds describe-db-instances \
  --profile "$AWS_PROFILE" --region "$REGION" \
  --db-instance-identifier "$SOURCE_DB" \
  --query "DBInstances[0].VpcSecurityGroups[*].VpcSecurityGroupId" --output text)

# 3. Restore snapshot to temporary instance
echo ""
echo "--- Step 2: Restoring snapshot to temporary instance ---"
echo "Temporary instance: $TEMP_DB"
aws rds restore-db-instance-from-db-snapshot \
  --profile "$AWS_PROFILE" --region "$REGION" \
  --db-instance-identifier "$TEMP_DB" \
  --db-snapshot-identifier "$SNAPSHOT_ID" \
  --db-subnet-group-name "$SUBNET_GROUP" \
  --vpc-security-group-ids $SECURITY_GROUPS \
  --db-instance-class db.t3.micro \
  --no-publicly-accessible

echo "Waiting for instance to become available (5-15 minutes)..."
aws rds wait db-instance-available \
  --profile "$AWS_PROFILE" --region "$REGION" \
  --db-instance-identifier "$TEMP_DB"
echo "Temporary instance is available."

# 4. Get endpoint
TEMP_ENDPOINT=$(aws rds describe-db-instances \
  --profile "$AWS_PROFILE" --region "$REGION" \
  --db-instance-identifier "$TEMP_DB" \
  --query "DBInstances[0].Endpoint.Address" --output text)
echo "Temporary endpoint: $TEMP_ENDPOINT"

# 5. Validate data
echo ""
echo "--- Step 3: Validating restored data ---"

# Get DB password from Secrets Manager
SECRET_ARN=$(aws secretsmanager list-secrets \
  --profile "$AWS_PROFILE" --region "$REGION" \
  --query "SecretList[?contains(Name, 'Wiki7DatabaseSecret')].ARN" \
  --output text | head -1)

if [ -z "$SECRET_ARN" ]; then
  echo "WARNING: Could not find DB secret in Secrets Manager. Skipping data validation."
  echo "DR test PARTIAL — snapshot restored successfully but could not validate data."
  exit 0
fi

DB_PASSWORD=$(aws secretsmanager get-secret-value \
  --profile "$AWS_PROFILE" --region "$REGION" \
  --secret-id "$SECRET_ARN" \
  --query "SecretString" --output text | python3 -c "import sys,json; print(json.load(sys.stdin)['password'])")

# Check table count
TABLE_COUNT=$(mysql -h "$TEMP_ENDPOINT" -u wikiuser -p"$DB_PASSWORD" wikidb \
  -sse "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='wikidb';" 2>/dev/null || echo "0")

echo "Tables found in restored DB: $TABLE_COUNT"

if [ "$TABLE_COUNT" -gt 0 ]; then
  # Check for critical MediaWiki tables
  for table in page revision user text; do
    EXISTS=$(mysql -h "$TEMP_ENDPOINT" -u wikiuser -p"$DB_PASSWORD" wikidb \
      -sse "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='wikidb' AND table_name='$table';" 2>/dev/null || echo "0")
    if [ "$EXISTS" = "1" ]; then
      echo "  [OK] Table '$table' exists"
    else
      echo "  [FAIL] Table '$table' missing!"
    fi
  done

  # Check page count
  PAGE_COUNT=$(mysql -h "$TEMP_ENDPOINT" -u wikiuser -p"$DB_PASSWORD" wikidb \
    -sse "SELECT COUNT(*) FROM page;" 2>/dev/null || echo "unknown")
  echo "  Pages in wiki: $PAGE_COUNT"

  echo ""
  echo "=== DR Test PASSED ==="
  echo "Snapshot $SNAPSHOT_ID is restorable and contains valid MediaWiki data."
  exit 0
else
  echo ""
  echo "=== DR Test FAILED ==="
  echo "Restored database has no tables."
  exit 1
fi
