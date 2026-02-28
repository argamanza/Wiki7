#!/bin/bash
set -euo pipefail

# Wiki7 DR Restore Script
# Restores the RDS database from a snapshot and triggers ECS redeployment.
#
# Usage:
#   ./dr-restore.sh                              # Restore from latest automated snapshot
#   ./dr-restore.sh --snapshot SNAPSHOT_ID        # Restore from a specific snapshot
#   ./dr-restore.sh --pitr "2026-01-15T10:30:00Z" # Point-in-time recovery
#
# Prerequisites:
#   - AWS CLI configured with appropriate permissions (profile: argamanza)
#   - jq installed

AWS_PROFILE="${AWS_PROFILE:-argamanza}"
REGION="${AWS_REGION:-il-central-1}"
DB_INSTANCE_ID="wiki7database"
CLUSTER_NAME="Wiki7Cluster"
SERVICE_NAME=""
RESTORE_MODE="snapshot"
SNAPSHOT_ID=""
PITR_TIMESTAMP=""
RESTORED_SUFFIX="-restored-$(date +%Y%m%d%H%M%S)"

usage() {
  echo "Usage: $0 [--snapshot SNAPSHOT_ID] [--pitr TIMESTAMP]"
  echo ""
  echo "Options:"
  echo "  --snapshot ID    Restore from a specific RDS snapshot"
  echo "  --pitr TIMESTAMP Point-in-time recovery (ISO 8601 format)"
  echo "  --help           Show this help message"
  exit 1
}

while [[ $# -gt 0 ]]; do
  case $1 in
    --snapshot) SNAPSHOT_ID="$2"; RESTORE_MODE="snapshot"; shift 2 ;;
    --pitr) PITR_TIMESTAMP="$2"; RESTORE_MODE="pitr"; shift 2 ;;
    --help) usage ;;
    *) echo "Unknown option: $1"; usage ;;
  esac
done

echo "=== Wiki7 DR Restore ==="
echo "Profile: $AWS_PROFILE | Region: $REGION | Mode: $RESTORE_MODE"

# 1. Find the source DB instance identifier
echo ""
echo "--- Step 1: Locating source DB instance ---"
SOURCE_DB=$(aws rds describe-db-instances \
  --profile "$AWS_PROFILE" --region "$REGION" \
  --query "DBInstances[?contains(DBInstanceIdentifier, 'wiki7')].DBInstanceIdentifier" \
  --output text | head -1)

if [ -z "$SOURCE_DB" ]; then
  echo "ERROR: Could not find Wiki7 RDS instance"
  exit 1
fi
echo "Source DB: $SOURCE_DB"

RESTORED_DB="${SOURCE_DB}${RESTORED_SUFFIX}"
echo "Restored DB: $RESTORED_DB"

# 2. Get the DB subnet group and security groups from the source
SUBNET_GROUP=$(aws rds describe-db-instances \
  --profile "$AWS_PROFILE" --region "$REGION" \
  --db-instance-identifier "$SOURCE_DB" \
  --query "DBInstances[0].DBSubnetGroup.DBSubnetGroupName" --output text)

SECURITY_GROUPS=$(aws rds describe-db-instances \
  --profile "$AWS_PROFILE" --region "$REGION" \
  --db-instance-identifier "$SOURCE_DB" \
  --query "DBInstances[0].VpcSecurityGroups[*].VpcSecurityGroupId" --output text)

# 3. Restore
echo ""
echo "--- Step 2: Restoring database ---"
if [ "$RESTORE_MODE" = "pitr" ]; then
  echo "Restoring to point-in-time: $PITR_TIMESTAMP"
  aws rds restore-db-instance-to-point-in-time \
    --profile "$AWS_PROFILE" --region "$REGION" \
    --source-db-instance-identifier "$SOURCE_DB" \
    --target-db-instance-identifier "$RESTORED_DB" \
    --restore-time "$PITR_TIMESTAMP" \
    --db-subnet-group-name "$SUBNET_GROUP" \
    --vpc-security-group-ids $SECURITY_GROUPS \
    --no-publicly-accessible
else
  # Find latest snapshot if not specified
  if [ -z "$SNAPSHOT_ID" ]; then
    echo "Finding latest automated snapshot..."
    SNAPSHOT_ID=$(aws rds describe-db-snapshots \
      --profile "$AWS_PROFILE" --region "$REGION" \
      --db-instance-identifier "$SOURCE_DB" \
      --snapshot-type automated \
      --query "sort_by(DBSnapshots, &SnapshotCreateTime)[-1].DBSnapshotIdentifier" \
      --output text)
    if [ "$SNAPSHOT_ID" = "None" ] || [ -z "$SNAPSHOT_ID" ]; then
      echo "ERROR: No automated snapshots found"
      exit 1
    fi
  fi
  echo "Restoring from snapshot: $SNAPSHOT_ID"
  aws rds restore-db-instance-from-db-snapshot \
    --profile "$AWS_PROFILE" --region "$REGION" \
    --db-instance-identifier "$RESTORED_DB" \
    --db-snapshot-identifier "$SNAPSHOT_ID" \
    --db-subnet-group-name "$SUBNET_GROUP" \
    --vpc-security-group-ids $SECURITY_GROUPS \
    --no-publicly-accessible
fi

# 4. Wait for restored instance
echo ""
echo "--- Step 3: Waiting for restored instance to become available ---"
echo "This may take 5-15 minutes..."
aws rds wait db-instance-available \
  --profile "$AWS_PROFILE" --region "$REGION" \
  --db-instance-identifier "$RESTORED_DB"
echo "Restored instance is available."

# 5. Get new endpoint
NEW_ENDPOINT=$(aws rds describe-db-instances \
  --profile "$AWS_PROFILE" --region "$REGION" \
  --db-instance-identifier "$RESTORED_DB" \
  --query "DBInstances[0].Endpoint.Address" --output text)
echo "New DB endpoint: $NEW_ENDPOINT"

# 6. Force ECS redeployment
echo ""
echo "--- Step 4: Forcing ECS redeployment ---"
echo "NOTE: You need to update the CDK stack to point to the new DB instance."
echo "  New endpoint: $NEW_ENDPOINT"
echo ""
echo "After updating the stack, run:"
echo "  npx cdk deploy Wiki7CdkStack --profile $AWS_PROFILE"
echo ""
echo "Or force a redeployment of the current service:"

# Find the ECS cluster and service
ECS_CLUSTER=$(aws ecs list-clusters \
  --profile "$AWS_PROFILE" --region "$REGION" \
  --query "clusterArns[?contains(@, 'Wiki7')]" --output text | head -1)

if [ -n "$ECS_CLUSTER" ]; then
  ECS_SERVICE=$(aws ecs list-services \
    --profile "$AWS_PROFILE" --region "$REGION" \
    --cluster "$ECS_CLUSTER" \
    --query "serviceArns[0]" --output text)
  echo "  aws ecs update-service --cluster $ECS_CLUSTER --service $ECS_SERVICE --force-new-deployment --profile $AWS_PROFILE --region $REGION"
fi

# 7. Health check
echo ""
echo "--- Step 5: Verify ---"
echo "Once ECS is redeployed, verify the wiki is functional:"
echo "  curl -s 'https://wiki7.co.il/api.php?action=query&meta=siteinfo&format=json' | jq ."
echo ""
echo "=== DR Restore complete ==="
echo "Restored instance: $RESTORED_DB"
echo "Old instance ($SOURCE_DB) is still running — delete it manually after verification."
