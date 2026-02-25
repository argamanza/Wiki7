import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as acm from 'aws-cdk-lib/aws-certificatemanager';
import * as route53 from 'aws-cdk-lib/aws-route53';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import { NetworkStack } from './network-stack';
import { DatabaseStack } from './database-stack';
import { BackupStack } from './backup-stack';
import { ApplicationStack } from './application-stack';
import { CloudFrontConstruct } from './cloudfront-stack';
import { MonitoringStack } from './monitoring-stack';

export interface Wiki7CdkStackProps extends cdk.StackProps {
  /** Domain name (parameterized, no longer hardcoded) */
  domainName: string;
  /** Enable managed RDS database (default: false, uses local MariaDB) */
  enableRds?: boolean;
  /** Enable Multi-AZ for RDS (only applies if enableRds is true) */
  enableMultiAz?: boolean;
  /** Enable private subnets with NAT Gateway (required for RDS in private subnet) */
  enablePrivateSubnets?: boolean;
  /** Enable CloudFront access logging */
  enableAccessLogging?: boolean;
  /** Email for alert notifications */
  alertEmail?: string;
  /** Monthly budget threshold in USD */
  budgetThresholdUsd?: number;
  /** SSH key pair name for EC2 access */
  keyPairName?: string;
}

/**
 * Main Wiki7 CDK stack - cost-conscious architecture for a personal fan wiki.
 *
 * Target cost: ~$16-20/mo (down from ~$107-128/mo)
 *
 * Architecture:
 *   CloudFront (CDN + basic protection)
 *       |
 *   t4g.small EC2 (2 vCPU, 2 GB RAM - ~$14/mo)
 *       |-- MediaWiki + PHP-FPM + Nginx
 *       |-- MariaDB (local, backed up to S3 daily)
 *       |-- 30 GB gp3 EBS (~$2.70/mo)
 *       |
 *   S3 bucket (media uploads, ~$0.15/mo)
 */
export class Wiki7CdkStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: Wiki7CdkStackProps) {
    super(scope, id, props);

    const {
      domainName,
      enableRds = false,
      enableMultiAz = false,
      enablePrivateSubnets = false,
      enableAccessLogging = true,
      alertEmail,
      budgetThresholdUsd = 25,
      keyPairName,
    } = props;

    // Import cross-region resources via SSM parameters
    const hostedZoneId = ssm.StringParameter.valueForStringParameter(
      this,
      '/wiki7/hostedzone/id'
    );
    const hostedZoneName = ssm.StringParameter.valueForStringParameter(
      this,
      '/wiki7/hostedzone/name'
    );

    const hostedZone = route53.HostedZone.fromHostedZoneAttributes(
      this,
      'ImportedZone',
      {
        hostedZoneId,
        zoneName: hostedZoneName,
      }
    );

    const certificateArn = ssm.StringParameter.valueForStringParameter(
      this,
      '/wiki7/certificate/arn'
    );
    const certificate = acm.Certificate.fromCertificateArn(
      this,
      'Wiki7Certificate',
      certificateArn
    );

    // Network: VPC with public subnets only (no NAT Gateway)
    const network = new NetworkStack(this, 'Network', {
      enablePrivateSubnets,
    });

    // Application: EC2 ASG + S3 (replaces ECS Fargate + ALB)
    const app = new ApplicationStack(this, 'Application', {
      vpc: network.vpc,
      ec2SecurityGroup: network.ec2SecurityGroup,
      domainName,
      keyPairName,
    });

    // Optional: Managed RDS database
    if (enableRds) {
      const database = new DatabaseStack(this, 'Database', {
        vpc: network.vpc,
        ec2SecurityGroup: network.ec2SecurityGroup,
        multiAz: enableMultiAz,
      });
    }

    // Backup: Daily mysqldump to S3 via Lambda + EventBridge
    new BackupStack(this, 'Backup', {
      backupBucket: app.mediawikiStorageBucket,
      autoScalingGroup: app.autoScalingGroup,
    });

    // CloudFront: CDN with direct EC2 origin (no ALB, no separate WAF)
    const cf = new CloudFrontConstruct(this, 'CloudFront', {
      autoScalingGroup: app.autoScalingGroup,
      hostedZone,
      certificate,
      domainName,
      mediawikiStorageBucket: app.mediawikiStorageBucket,
      enableAccessLogging,
    });

    // Monitoring: SNS + CloudWatch alarms + Budget (only if email provided)
    if (alertEmail) {
      new MonitoringStack(this, 'Monitoring', {
        alertEmail,
        autoScalingGroup: app.autoScalingGroup,
        distribution: cf.distribution,
        budgetThresholdUsd,
      });
    }

    // Global resource tags for cost allocation
    cdk.Tags.of(this).add('Project', 'Wiki7');
    cdk.Tags.of(this).add('Environment', 'production');
    cdk.Tags.of(this).add('ManagedBy', 'CDK');
  }
}
