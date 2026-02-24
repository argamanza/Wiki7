import * as cdk from 'aws-cdk-lib';
import * as assertions from 'aws-cdk-lib/assertions';
import { NetworkStack } from '../lib/network-stack';
import { DatabaseStack } from '../lib/database-stack';
import { ApplicationStack } from '../lib/application-stack';
import { CloudFrontConstruct } from '../lib/cloudfront-stack';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as elbv2 from 'aws-cdk-lib/aws-elasticloadbalancingv2';
import * as route53 from 'aws-cdk-lib/aws-route53';
import * as acm from 'aws-cdk-lib/aws-certificatemanager';
import * as s3 from 'aws-cdk-lib/aws-s3';

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

  test('MediaWiki security group exists', () => {
    const template = assertions.Template.fromStack(stack);
    template.hasResourceProperties('AWS::EC2::SecurityGroup', {
      GroupDescription: 'Allow inbound traffic from ALB to MediaWiki containers',
    });
  });

  test('Database security group exists', () => {
    const template = assertions.Template.fromStack(stack);
    template.hasResourceProperties('AWS::EC2::SecurityGroup', {
      GroupDescription: 'Allow ECS containers to connect to MariaDB',
    });
  });
});

describe('DatabaseStack', () => {
  let stack: cdk.Stack;

  beforeAll(() => {
    const app = new cdk.App();
    stack = new cdk.Stack(app, 'TestDatabaseStack');

    const network = new NetworkStack(stack, 'Network');

    new DatabaseStack(stack, 'Database', {
      vpc: network.vpc,
      mediawikiSecurityGroup: network.mediawikiSecurityGroup,
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

  test('Database credentials secret is created', () => {
    const template = assertions.Template.fromStack(stack);
    template.hasResourceProperties('AWS::SecretsManager::Secret', {
      Description: 'Database credentials for Wiki7 MediaWiki database',
    });
  });
});

describe('ApplicationStack', () => {
  let stack: cdk.Stack;

  beforeAll(() => {
    const app = new cdk.App();
    stack = new cdk.Stack(app, 'TestApplicationStack');

    const network = new NetworkStack(stack, 'Network');
    const database = new DatabaseStack(stack, 'Database', {
      vpc: network.vpc,
      mediawikiSecurityGroup: network.mediawikiSecurityGroup,
    });

    new ApplicationStack(stack, 'Application', {
      vpc: network.vpc,
      dbInstance: database.dbInstance,
      dbSecret: database.dbSecret,
      mediawikiSecurityGroup: network.mediawikiSecurityGroup,
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

  test('ECS cluster is created', () => {
    const template = assertions.Template.fromStack(stack);
    template.resourceCountIs('AWS::ECS::Cluster', 1);
  });

  test('Fargate task definition is created', () => {
    const template = assertions.Template.fromStack(stack);
    template.hasResourceProperties('AWS::ECS::TaskDefinition', {
      Cpu: '512',
      Memory: '1024',
      NetworkMode: 'awsvpc',
      RequiresCompatibilities: ['FARGATE'],
    });
  });

  test('Fargate service is created', () => {
    const template = assertions.Template.fromStack(stack);
    template.hasResourceProperties('AWS::ECS::Service', {
      LaunchType: 'FARGATE',
      DesiredCount: 1,
    });
  });

  test('Application Load Balancer is created', () => {
    const template = assertions.Template.fromStack(stack);
    template.hasResourceProperties('AWS::ElasticLoadBalancingV2::LoadBalancer', {
      Scheme: 'internet-facing',
      Name: 'Wiki7Alb',
    });
  });

  test('ALB listener on port 80 is created', () => {
    const template = assertions.Template.fromStack(stack);
    template.hasResourceProperties('AWS::ElasticLoadBalancingV2::Listener', {
      Port: 80,
      Protocol: 'HTTP',
    });
  });
});

describe('CloudFrontStack', () => {
  let stack: cdk.Stack;

  beforeAll(() => {
    const app = new cdk.App();
    stack = new cdk.Stack(app, 'TestCloudFrontStack');

    const vpc = new ec2.Vpc(stack, 'TestVpc');

    const albSg = new ec2.SecurityGroup(stack, 'AlbSg', { vpc });
    const alb = new elbv2.ApplicationLoadBalancer(stack, 'TestAlb', {
      vpc,
      internetFacing: true,
      securityGroup: albSg,
    });

    const hostedZone = route53.HostedZone.fromHostedZoneAttributes(stack, 'TestZone', {
      hostedZoneId: 'Z1234567890',
      zoneName: 'wiki7.co.il',
    });

    const certificate = acm.Certificate.fromCertificateArn(
      stack,
      'TestCert',
      'arn:aws:acm:us-east-1:123456789012:certificate/test-cert-id'
    );

    const bucket = new s3.Bucket(stack, 'TestBucket');

    new CloudFrontConstruct(stack, 'CloudFront', {
      alb,
      hostedZone,
      certificate,
      domainName: 'wiki7.co.il',
      mediawikiStorageBucket: bucket,
      wafWebAclArn: 'arn:aws:wafv2:us-east-1:123456789012:global/webacl/test/test-id',
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

  test('CloudFront distribution has WAF associated', () => {
    const template = assertions.Template.fromStack(stack);
    template.hasResourceProperties('AWS::CloudFront::Distribution', {
      DistributionConfig: {
        WebACLId: 'arn:aws:wafv2:us-east-1:123456789012:global/webacl/test/test-id',
      },
    });
  });

  test('DNS records are created for apex and www', () => {
    const template = assertions.Template.fromStack(stack);
    template.resourceCountIs('AWS::Route53::RecordSet', 2);
  });
});
