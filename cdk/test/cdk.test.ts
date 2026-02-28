import * as cdk from 'aws-cdk-lib';
import { Template, Match } from 'aws-cdk-lib/assertions';
import { NetworkStack } from '../lib/network-stack';
import { DatabaseStack } from '../lib/database-stack';
import { ApplicationStack } from '../lib/application-stack';
import { BackupStack } from '../lib/backup-stack';

// Helper: create a stack with NetworkStack construct
function createNetworkStack(): { stack: cdk.Stack; network: NetworkStack } {
  const app = new cdk.App();
  const stack = new cdk.Stack(app, 'TestStack');
  const network = new NetworkStack(stack, 'Network');
  return { stack, network };
}

describe('NetworkStack', () => {
  let template: Template;

  beforeAll(() => {
    const { stack } = createNetworkStack();
    template = Template.fromStack(stack);
  });

  test('creates a VPC', () => {
    template.resourceCountIs('AWS::EC2::VPC', 1);
  });

  test('creates public and private subnets', () => {
    template.hasResourceProperties('AWS::EC2::Subnet', {
      MapPublicIpOnLaunch: true,
    });
  });

  test('has no NAT gateway (cost optimization)', () => {
    template.resourceCountIs('AWS::EC2::NatGateway', 0);
  });

  test('creates S3 VPC gateway endpoint', () => {
    template.hasResourceProperties('AWS::EC2::VPCEndpoint', {
      ServiceName: Match.objectLike({}),
      VpcEndpointType: 'Gateway',
    });
  });

  test('creates MediaWiki security group', () => {
    template.hasResourceProperties('AWS::EC2::SecurityGroup', {
      GroupDescription: Match.stringLikeRegexp('.*MediaWiki.*'),
    });
  });

  test('creates Database security group', () => {
    template.hasResourceProperties('AWS::EC2::SecurityGroup', {
      GroupDescription: Match.stringLikeRegexp('.*MariaDB.*'),
    });
  });

  test('allows ECS to connect to RDS on port 3306', () => {
    template.hasResourceProperties('AWS::EC2::SecurityGroupIngress', {
      IpProtocol: 'tcp',
      FromPort: 3306,
      ToPort: 3306,
    });
  });
});

describe('DatabaseStack', () => {
  let template: Template;

  beforeAll(() => {
    const { stack, network } = createNetworkStack();
    new DatabaseStack(stack, 'Database', {
      vpc: network.vpc,
      mediawikiSecurityGroup: network.mediawikiSecurityGroup,
    });
    template = Template.fromStack(stack);
  });

  test('creates RDS instance', () => {
    template.resourceCountIs('AWS::RDS::DBInstance', 1);
  });

  test('uses MariaDB engine', () => {
    template.hasResourceProperties('AWS::RDS::DBInstance', {
      Engine: 'mariadb',
    });
  });

  test('uses t3.micro instance class', () => {
    template.hasResourceProperties('AWS::RDS::DBInstance', {
      DBInstanceClass: 'db.t3.micro',
    });
  });

  test('enables storage encryption', () => {
    template.hasResourceProperties('AWS::RDS::DBInstance', {
      StorageEncrypted: true,
    });
  });

  test('creates Secrets Manager secret for DB credentials', () => {
    template.hasResourceProperties('AWS::SecretsManager::Secret', {
      Description: 'Database credentials for Wiki7 MediaWiki database',
    });
  });
});

describe('ApplicationStack', () => {
  let template: Template;

  beforeAll(() => {
    const app = new cdk.App();
    const stack = new cdk.Stack(app, 'TestAppStack');
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
    template = Template.fromStack(stack);
  });

  test('creates ECS cluster', () => {
    template.resourceCountIs('AWS::ECS::Cluster', 1);
  });

  test('creates Fargate task definition', () => {
    template.hasResourceProperties('AWS::ECS::TaskDefinition', {
      RequiresCompatibilities: ['FARGATE'],
      Cpu: '512',
      Memory: '1024',
    });
  });

  test('creates ECS Fargate service', () => {
    template.hasResourceProperties('AWS::ECS::Service', {
      LaunchType: 'FARGATE',
      DesiredCount: 1,
    });
  });

  test('creates S3 storage bucket with versioning', () => {
    template.hasResourceProperties('AWS::S3::Bucket', {
      VersioningConfiguration: {
        Status: 'Enabled',
      },
    });
  });

  test('creates Application Load Balancer', () => {
    template.resourceCountIs('AWS::ElasticLoadBalancingV2::LoadBalancer', 1);
  });

  test('creates ALB listener on port 80', () => {
    template.hasResourceProperties('AWS::ElasticLoadBalancingV2::Listener', {
      Port: 80,
      Protocol: 'HTTP',
    });
  });

  test('health check uses MediaWiki API endpoint', () => {
    template.hasResourceProperties('AWS::ElasticLoadBalancingV2::TargetGroup', {
      HealthCheckPath: '/api.php?action=query&meta=siteinfo&format=json',
      Matcher: { HttpCode: '200' },
    });
  });

  test('ECS service has health check grace period', () => {
    template.hasResourceProperties('AWS::ECS::Service', {
      HealthCheckGracePeriodSeconds: 300,
    });
  });

  test('creates MediaWiki application secret', () => {
    template.hasResourceProperties('AWS::SecretsManager::Secret', {
      Description: 'MediaWiki application secrets (admin password, secret key, upgrade key)',
    });
  });

  test('container has MediaWiki secrets injected', () => {
    template.hasResourceProperties('AWS::ECS::TaskDefinition', {
      ContainerDefinitions: Match.arrayWith([
        Match.objectLike({
          Secrets: Match.arrayWith([
            Match.objectLike({ Name: 'MEDIAWIKI_DB_PASSWORD' }),
            Match.objectLike({ Name: 'MEDIAWIKI_ADMIN_PASSWORD' }),
            Match.objectLike({ Name: 'WG_SECRET_KEY' }),
            Match.objectLike({ Name: 'WG_UPGRADE_KEY' }),
          ]),
        }),
      ]),
    });
  });
});

describe('BackupStack', () => {
  let template: Template;

  beforeAll(() => {
    const { stack, network } = createNetworkStack();
    const database = new DatabaseStack(stack, 'Database', {
      vpc: network.vpc,
      mediawikiSecurityGroup: network.mediawikiSecurityGroup,
    });
    new BackupStack(stack, 'Backup', {
      dbInstance: database.dbInstance,
    });
    template = Template.fromStack(stack);
  });

  test('creates backup vault', () => {
    template.resourceCountIs('AWS::Backup::BackupVault', 1);
  });

  test('creates backup plan', () => {
    template.resourceCountIs('AWS::Backup::BackupPlan', 1);
  });

  test('creates KMS key for backup encryption', () => {
    template.hasResourceProperties('AWS::KMS::Key', {
      EnableKeyRotation: true,
    });
  });
});
