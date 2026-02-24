import { Construct } from 'constructs';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import * as rds from 'aws-cdk-lib/aws-rds';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as cdk from 'aws-cdk-lib';

export interface DatabaseStackProps {
  vpc: ec2.Vpc;
  ec2SecurityGroup: ec2.SecurityGroup;
  /** Enable Multi-AZ deployment (doubles RDS cost, adds ~$15/mo) */
  multiAz?: boolean;
  /** RDS instance class (default: t3.micro for cost savings) */
  instanceSize?: ec2.InstanceSize;
}

/**
 * Optional RDS database stack.
 *
 * Default architecture uses local MariaDB on EC2 with S3 backup.
 * Enable this stack when you need a managed database (e.g., for multi-instance setups).
 *
 * Cost: ~$15-30/mo depending on instance size and Multi-AZ setting.
 */
export class DatabaseStack extends Construct {
  readonly dbInstance: rds.DatabaseInstance;
  readonly dbSecret: secretsmanager.Secret;

  constructor(scope: Construct, id: string, props: DatabaseStackProps) {
    super(scope, id);

    const { vpc, ec2SecurityGroup } = props;
    const multiAz = props.multiAz ?? false;
    const instanceSize = props.instanceSize ?? ec2.InstanceSize.MICRO;

    // Create secret for DB credentials
    this.dbSecret = new secretsmanager.Secret(this, 'Wiki7DatabaseSecret', {
      generateSecretString: {
        secretStringTemplate: JSON.stringify({ username: 'wikiuser' }),
        generateStringKey: 'password',
        excludePunctuation: true,
        includeSpace: false,
      },
      description: 'Database credentials for Wiki7 MediaWiki database',
    });

    // Database security group
    const dbSecurityGroup = new ec2.SecurityGroup(
      this,
      'Wiki7DatabaseSecurityGroup',
      {
        vpc,
        description: 'Allow EC2 instances to connect to RDS MariaDB',
        allowAllOutbound: false,
      }
    );

    // Allow EC2 security group to access RDS on port 3306
    dbSecurityGroup.addIngressRule(
      ec2SecurityGroup,
      ec2.Port.tcp(3306),
      'Allow EC2 MediaWiki instances to access RDS database'
    );

    // Create RDS instance
    this.dbInstance = new rds.DatabaseInstance(this, 'Wiki7Database', {
      engine: rds.DatabaseInstanceEngine.mariaDb({
        version: rds.MariaDbEngineVersion.VER_10_5,
      }),
      vpc,
      vpcSubnets: { subnetType: ec2.SubnetType.PUBLIC },
      securityGroups: [dbSecurityGroup],
      credentials: rds.Credentials.fromSecret(this.dbSecret),
      multiAz,
      allocatedStorage: 20,
      maxAllocatedStorage: 100,
      instanceType: ec2.InstanceType.of(
        ec2.InstanceClass.BURSTABLE3,
        instanceSize
      ),
      publiclyAccessible: false,
      removalPolicy: cdk.RemovalPolicy.SNAPSHOT,
      deletionProtection: true,
      backupRetention: cdk.Duration.days(7),
      databaseName: 'wikidb',
      storageEncrypted: true,
    });

    // Allow MediaWiki EC2 instances to connect to RDS
    this.dbInstance.connections.allowFrom(
      ec2SecurityGroup,
      ec2.Port.tcp(3306),
      'Allow MediaWiki EC2 to connect to RDS'
    );

    // Tags for cost tracking
    cdk.Tags.of(this.dbInstance).add('Project', 'Wiki7');
    cdk.Tags.of(this.dbInstance).add('Component', 'Database');

    // Outputs
    new cdk.CfnOutput(this, 'DatabaseEndpoint', {
      value: this.dbInstance.dbInstanceEndpointAddress,
      description: 'RDS database endpoint',
    });
  }
}
