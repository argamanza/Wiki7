import { Construct } from 'constructs';
import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as events from 'aws-cdk-lib/aws-events';
import * as eventsTargets from 'aws-cdk-lib/aws-events-targets';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as autoscaling from 'aws-cdk-lib/aws-autoscaling';
import * as path from 'path';

export interface BackupStackProps {
  /** S3 bucket to store database backups */
  backupBucket: s3.Bucket;
  /** Auto Scaling Group to run backup commands on */
  autoScalingGroup: autoscaling.AutoScalingGroup;
  /** Number of days to retain backups (default: 7) */
  retentionDays?: number;
}

/**
 * Automated backup stack using SSM Run Command to execute mysqldump on EC2,
 * then upload to S3 via a daily EventBridge cron rule.
 *
 * This replaces the enterprise-grade AWS Backup + KMS setup with a
 * cost-effective approach for a personal project.
 */
export class BackupStack extends Construct {
  constructor(scope: Construct, id: string, props: BackupStackProps) {
    super(scope, id);

    const { backupBucket, autoScalingGroup } = props;
    const retentionDays = props.retentionDays ?? 7;

    // Add lifecycle rule to auto-expire old backups
    backupBucket.addLifecycleRule({
      id: 'ExpireOldBackups',
      prefix: 'backups/',
      enabled: true,
      expiration: cdk.Duration.days(retentionDays),
    });

    // Lambda function for automated database backup
    const backupRole = new iam.Role(this, 'BackupLambdaRole', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName(
          'service-role/AWSLambdaBasicExecutionRole'
        ),
      ],
    });

    // Grant SSM Run Command permissions
    backupRole.addToPolicy(
      new iam.PolicyStatement({
        actions: [
          'ssm:SendCommand',
          'ssm:GetCommandInvocation',
        ],
        resources: ['*'],
      })
    );

    // Grant S3 write access for backups
    backupBucket.grantWrite(backupRole, 'backups/*');

    // Grant EC2 describe permissions to find ASG instances
    backupRole.addToPolicy(
      new iam.PolicyStatement({
        actions: [
          'autoscaling:DescribeAutoScalingGroups',
          'ec2:DescribeInstances',
        ],
        resources: ['*'],
      })
    );

    const backupFunction = new lambda.Function(this, 'BackupLambda', {
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'db_backup.lambda_handler',
      code: lambda.Code.fromAsset(
        path.join(__dirname, '../lambda/db-backup')
      ),
      timeout: cdk.Duration.minutes(5),
      role: backupRole,
      environment: {
        BACKUP_BUCKET: backupBucket.bucketName,
        ASG_NAME: autoScalingGroup.autoScalingGroupName,
        RETENTION_DAYS: retentionDays.toString(),
      },
    });

    // EventBridge rule: daily at 01:00 UTC
    new events.Rule(this, 'DailyBackupRule', {
      ruleName: 'wiki7-daily-backup',
      description: 'Trigger daily database backup (mysqldump to S3)',
      schedule: events.Schedule.cron({ hour: '1', minute: '0' }),
      targets: [new eventsTargets.LambdaFunction(backupFunction)],
    });

    // Tags
    cdk.Tags.of(this).add('Project', 'Wiki7');
    cdk.Tags.of(this).add('Component', 'Backup');
  }
}
