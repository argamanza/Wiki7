import * as cdk from 'aws-cdk-lib';
import * as assertions from 'aws-cdk-lib/assertions';
import { NetworkStack } from '../lib/network-stack';
import { DatabaseStack } from '../lib/database-stack';
import { ApplicationStack } from '../lib/application-stack';
import { CloudFrontConstruct } from '../lib/cloudfront-stack';
import { BackupStack } from '../lib/backup-stack';
import { MonitoringStack } from '../lib/monitoring-stack';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as autoscaling from 'aws-cdk-lib/aws-autoscaling';
import * as route53 from 'aws-cdk-lib/aws-route53';
import * as acm from 'aws-cdk-lib/aws-certificatemanager';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as cloudfront from 'aws-cdk-lib/aws-cloudfront';

describe('NetworkStack', () => {
  let stack: cdk.Stack;

  beforeAll(() => {
    const app = new cdk.App();
    stack = new cdk.Stack(app, 'TestNetworkStack');
    new NetworkStack(stack, 'Network');
  });

  test('VPC is created', () => {
    const template = assertions.Template.fromStack(stack);
    template.resourceCountIs('AWS::EC2::VPC', 1);
  });

  test('VPC has correct configuration', () => {
    const template = assertions.Template.fromStack(stack);
    template.hasResourceProperties('AWS::EC2::VPC', {
      EnableDnsHostnames: true,
      EnableDnsSupport: true,
    });
  });

  test('No NAT Gateway by default (cost savings)', () => {
    const template = assertions.Template.fromStack(stack);
    template.resourceCountIs('AWS::EC2::NatGateway', 0);
  });

  test('S3 VPC Gateway Endpoint is created (free)', () => {
    const template = assertions.Template.fromStack(stack);
    template.hasResourceProperties('AWS::EC2::VPCEndpoint', {
      ServiceName: {
        'Fn::Join': [
          '',
          [
            'com.amazonaws.',
            { Ref: 'AWS::Region' },
            '.s3',
          ],
        ],
      },
      VpcEndpointType: 'Gateway',
    });
  });

  test('EC2 security group exists', () => {
    const template = assertions.Template.fromStack(stack);
    template.hasResourceProperties('AWS::EC2::SecurityGroup', {
      GroupDescription:
        'Allow inbound HTTP from CloudFront and outbound for updates',
    });
  });
});

describe('NetworkStack with private subnets', () => {
  let stack: cdk.Stack;

  beforeAll(() => {
    const app = new cdk.App();
    stack = new cdk.Stack(app, 'TestNetworkStackPrivate');
    new NetworkStack(stack, 'Network', { enablePrivateSubnets: true });
  });

  test('NAT Gateway is created when private subnets enabled', () => {
    const template = assertions.Template.fromStack(stack);
    template.resourceCountIs('AWS::EC2::NatGateway', 1);
  });
});

describe('ApplicationStack', () => {
  let stack: cdk.Stack;

  beforeAll(() => {
    const app = new cdk.App();
    stack = new cdk.Stack(app, 'TestApplicationStack');

    const network = new NetworkStack(stack, 'Network');

    new ApplicationStack(stack, 'Application', {
      vpc: network.vpc,
      ec2SecurityGroup: network.ec2SecurityGroup,
      domainName: 'wiki7.co.il',
    });
  });

  test('S3 bucket is created with block public access', () => {
    const template = assertions.Template.fromStack(stack);
    template.hasResourceProperties('AWS::S3::Bucket', {
      PublicAccessBlockConfiguration: {
        BlockPublicAcls: true,
        BlockPublicPolicy: true,
        IgnorePublicAcls: true,
        RestrictPublicBuckets: true,
      },
    });
  });

  test('EC2 Launch Template is created with t4g.small', () => {
    const template = assertions.Template.fromStack(stack);
    template.hasResourceProperties('AWS::EC2::LaunchTemplate', {
      LaunchTemplateData: {
        InstanceType: 't4g.small',
      },
    });
  });

  test('Launch Template requires IMDSv2', () => {
    const template = assertions.Template.fromStack(stack);
    template.hasResourceProperties('AWS::EC2::LaunchTemplate', {
      LaunchTemplateData: {
        MetadataOptions: {
          HttpTokens: 'required',
        },
      },
    });
  });

  test('Auto Scaling Group is created with correct capacity', () => {
    const template = assertions.Template.fromStack(stack);
    template.hasResourceProperties('AWS::AutoScaling::AutoScalingGroup', {
      MinSize: '1',
      MaxSize: '2',
      DesiredCapacity: '1',
    });
  });

  test('No ALB is created (cost savings)', () => {
    const template = assertions.Template.fromStack(stack);
    template.resourceCountIs(
      'AWS::ElasticLoadBalancingV2::LoadBalancer',
      0
    );
  });

  test('No ECS cluster is created (replaced by EC2)', () => {
    const template = assertions.Template.fromStack(stack);
    template.resourceCountIs('AWS::ECS::Cluster', 0);
  });

  test('No Fargate task definition is created', () => {
    const template = assertions.Template.fromStack(stack);
    template.resourceCountIs('AWS::ECS::TaskDefinition', 0);
  });

  test('EC2 IAM role has SSM managed policy', () => {
    const template = assertions.Template.fromStack(stack);
    template.hasResourceProperties('AWS::IAM::Role', {
      ManagedPolicyArns: assertions.Match.arrayWith([
        {
          'Fn::Join': assertions.Match.anyValue(),
        },
      ]),
    });
  });
});

describe('DatabaseStack (optional)', () => {
  let stack: cdk.Stack;

  beforeAll(() => {
    const app = new cdk.App();
    stack = new cdk.Stack(app, 'TestDatabaseStack');

    const network = new NetworkStack(stack, 'Network');

    new DatabaseStack(stack, 'Database', {
      vpc: network.vpc,
      ec2SecurityGroup: network.ec2SecurityGroup,
    });
  });

  test('RDS instance is created with MariaDB engine', () => {
    const template = assertions.Template.fromStack(stack);
    template.hasResourceProperties('AWS::RDS::DBInstance', {
      Engine: 'mariadb',
    });
  });

  test('RDS instance has deletion protection enabled', () => {
    const template = assertions.Template.fromStack(stack);
    template.hasResourceProperties('AWS::RDS::DBInstance', {
      DeletionProtection: true,
    });
  });

  test('RDS instance has storage encryption enabled', () => {
    const template = assertions.Template.fromStack(stack);
    template.hasResourceProperties('AWS::RDS::DBInstance', {
      StorageEncrypted: true,
    });
  });

  test('RDS instance is not publicly accessible', () => {
    const template = assertions.Template.fromStack(stack);
    template.hasResourceProperties('AWS::RDS::DBInstance', {
      PubliclyAccessible: false,
    });
  });

  test('RDS instance is single-AZ by default', () => {
    const template = assertions.Template.fromStack(stack);
    template.hasResourceProperties('AWS::RDS::DBInstance', {
      MultiAZ: false,
    });
  });

  test('Database credentials secret is created', () => {
    const template = assertions.Template.fromStack(stack);
    template.hasResourceProperties('AWS::SecretsManager::Secret', {
      Description: 'Database credentials for Wiki7 MediaWiki database',
    });
  });
});

describe('CloudFrontStack', () => {
  let stack: cdk.Stack;

  beforeAll(() => {
    const app = new cdk.App();
    stack = new cdk.Stack(app, 'TestCloudFrontStack');

    const vpc = new ec2.Vpc(stack, 'TestVpc');
    const sg = new ec2.SecurityGroup(stack, 'TestSg', { vpc });

    const asg = new autoscaling.AutoScalingGroup(stack, 'TestASG', {
      vpc,
      instanceType: ec2.InstanceType.of(
        ec2.InstanceClass.T4G,
        ec2.InstanceSize.SMALL
      ),
      machineImage: ec2.MachineImage.latestAmazonLinux2023({
        cpuType: ec2.AmazonLinuxCpuType.ARM_64,
      }),
    });

    const hostedZone = route53.HostedZone.fromHostedZoneAttributes(
      stack,
      'TestZone',
      {
        hostedZoneId: 'Z1234567890',
        zoneName: 'wiki7.co.il',
      }
    );

    const certificate = acm.Certificate.fromCertificateArn(
      stack,
      'TestCert',
      'arn:aws:acm:us-east-1:123456789012:certificate/test-cert-id'
    );

    const bucket = new s3.Bucket(stack, 'TestBucket');

    new CloudFrontConstruct(stack, 'CloudFront', {
      autoScalingGroup: asg,
      hostedZone,
      certificate,
      domainName: 'wiki7.co.il',
      mediawikiStorageBucket: bucket,
    });
  });

  test('CloudFront distribution is created', () => {
    const template = assertions.Template.fromStack(stack);
    template.resourceCountIs('AWS::CloudFront::Distribution', 1);
  });

  test('CloudFront distribution has correct domain names', () => {
    const template = assertions.Template.fromStack(stack);
    template.hasResourceProperties('AWS::CloudFront::Distribution', {
      DistributionConfig: {
        Aliases: ['wiki7.co.il', 'www.wiki7.co.il'],
      },
    });
  });

  test('No WAF is associated (cost savings)', () => {
    const template = assertions.Template.fromStack(stack);
    // Verify the distribution does NOT have a WebACLId
    const distributions = template.findResources(
      'AWS::CloudFront::Distribution'
    );
    for (const [, resource] of Object.entries(distributions)) {
      const config = (resource as any).Properties?.DistributionConfig;
      expect(config?.WebACLId).toBeUndefined();
    }
  });

  test('CloudFront uses PriceClass 100 (cost optimization)', () => {
    const template = assertions.Template.fromStack(stack);
    template.hasResourceProperties('AWS::CloudFront::Distribution', {
      DistributionConfig: {
        PriceClass: 'PriceClass_100',
      },
    });
  });

  test('DNS records are created for apex and www', () => {
    const template = assertions.Template.fromStack(stack);
    template.resourceCountIs('AWS::Route53::RecordSet', 2);
  });
});

describe('BackupStack', () => {
  let stack: cdk.Stack;

  beforeAll(() => {
    const app = new cdk.App();
    stack = new cdk.Stack(app, 'TestBackupStack');

    const vpc = new ec2.Vpc(stack, 'TestVpc');

    const asg = new autoscaling.AutoScalingGroup(stack, 'TestASG', {
      vpc,
      instanceType: ec2.InstanceType.of(
        ec2.InstanceClass.T4G,
        ec2.InstanceSize.SMALL
      ),
      machineImage: ec2.MachineImage.latestAmazonLinux2023({
        cpuType: ec2.AmazonLinuxCpuType.ARM_64,
      }),
    });

    const bucket = new s3.Bucket(stack, 'TestBucket');

    new BackupStack(stack, 'Backup', {
      backupBucket: bucket,
      autoScalingGroup: asg,
    });
  });

  test('Backup Lambda function is created', () => {
    const template = assertions.Template.fromStack(stack);
    template.hasResourceProperties('AWS::Lambda::Function', {
      Handler: 'db_backup.lambda_handler',
      Runtime: 'python3.11',
    });
  });

  test('EventBridge rule for daily backup is created', () => {
    const template = assertions.Template.fromStack(stack);
    template.hasResourceProperties('AWS::Events::Rule', {
      ScheduleExpression: 'cron(0 1 * * ? *)',
    });
  });

  test('No AWS Backup vault (replaced by Lambda backup)', () => {
    const template = assertions.Template.fromStack(stack);
    template.resourceCountIs('AWS::Backup::BackupVault', 0);
  });

  test('No KMS key (cost savings)', () => {
    const template = assertions.Template.fromStack(stack);
    template.resourceCountIs('AWS::KMS::Key', 0);
  });
});

describe('MonitoringStack', () => {
  let stack: cdk.Stack;

  beforeAll(() => {
    const app = new cdk.App();
    stack = new cdk.Stack(app, 'TestMonitoringStack');

    const vpc = new ec2.Vpc(stack, 'TestVpc');

    const asg = new autoscaling.AutoScalingGroup(stack, 'TestASG', {
      vpc,
      instanceType: ec2.InstanceType.of(
        ec2.InstanceClass.T4G,
        ec2.InstanceSize.SMALL
      ),
      machineImage: ec2.MachineImage.latestAmazonLinux2023({
        cpuType: ec2.AmazonLinuxCpuType.ARM_64,
      }),
    });

    // Create a mock CloudFront distribution for monitoring
    const bucket = new s3.Bucket(stack, 'TestBucket');
    const distribution = new cloudfront.Distribution(
      stack,
      'TestDistribution',
      {
        defaultBehavior: {
          origin: new (require('aws-cdk-lib/aws-cloudfront-origins').S3BucketOrigin)(bucket),
        },
      }
    );

    new MonitoringStack(stack, 'Monitoring', {
      alertEmail: 'test@example.com',
      autoScalingGroup: asg,
      distribution,
    });
  });

  test('SNS topic is created', () => {
    const template = assertions.Template.fromStack(stack);
    template.hasResourceProperties('AWS::SNS::Topic', {
      TopicName: 'wiki7-alerts',
    });
  });

  test('Email subscription is created', () => {
    const template = assertions.Template.fromStack(stack);
    template.hasResourceProperties('AWS::SNS::Subscription', {
      Protocol: 'email',
      Endpoint: 'test@example.com',
    });
  });

  test('CloudWatch alarms are created', () => {
    const template = assertions.Template.fromStack(stack);
    // CPU alarm, disk alarm, CloudFront error alarm = 3 alarms
    template.resourceCountIs('AWS::CloudWatch::Alarm', 3);
  });

  test('CPU alarm has correct threshold', () => {
    const template = assertions.Template.fromStack(stack);
    template.hasResourceProperties('AWS::CloudWatch::Alarm', {
      AlarmName: 'wiki7-ec2-cpu-high',
      Threshold: 80,
    });
  });

  test('Budget is created with default $25 threshold', () => {
    const template = assertions.Template.fromStack(stack);
    template.hasResourceProperties('AWS::Budgets::Budget', {
      Budget: {
        BudgetLimit: {
          Amount: 25,
          Unit: 'USD',
        },
        BudgetType: 'COST',
        TimeUnit: 'MONTHLY',
      },
    });
  });
});
