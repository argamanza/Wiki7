import { Construct } from 'constructs';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import * as rds from 'aws-cdk-lib/aws-rds';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as cdk from 'aws-cdk-lib';

interface DatabaseStackProps {
  vpc: ec2.Vpc;
  mediawikiSecurityGroup: ec2.SecurityGroup;
}

export class DatabaseStack extends Construct {
  readonly dbInstance: rds.DatabaseInstance;
  readonly dbSecret: secretsmanager.Secret;

  constructor(scope: Construct, id: string, props: DatabaseStackProps) {
    super(scope, id);

    const { vpc, mediawikiSecurityGroup } = props;

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

    // Create RDS instance
    this.dbInstance = new rds.DatabaseInstance(this, 'Wiki7Database', {
      engine: rds.DatabaseInstanceEngine.mariaDb({ version: rds.MariaDbEngineVersion.VER_10_5 }),
      vpc,
      vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS },
      securityGroups: [mediawikiSecurityGroup],
      credentials: rds.Credentials.fromSecret(this.dbSecret),
      multiAz: false,
      allocatedStorage: 20,
      maxAllocatedStorage: 100,
      instanceType: ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.MICRO),
      publiclyAccessible: false,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      deletionProtection: false,
      backupRetention: cdk.Duration.days(7),
      databaseName: 'wikidb',
    });
  }
}
