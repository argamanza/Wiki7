import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { DnsStack } from './dns-stack';
import { NetworkStack } from './network-stack'
import { DatabaseStack } from './database-stack';
import { BackupStack } from './backup-stack';
import { ApplicationStack } from './application-stack';

export class Wiki7CdkStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

      // Provision DNS (Route 53 Hosted Zone)
      const dns = new DnsStack(this, 'Dns', {
        domainName: 'wiki7.co.il',
      });    

    // Provision networking resources (VPC and SGs)
    const network = new NetworkStack(this, 'Network');

    // Provision RDS database and secrets
    const database = new DatabaseStack(this, 'Database', {
      vpc: network.vpc,
      mediawikiSecurityGroup: network.mediawikiSecurityGroup,
    });

    const backup = new BackupStack(this, 'Backup', {
      dbInstance: database.dbInstance,
    });

    // Provision ECS cluster, task, service, ALB
    new ApplicationStack(this, 'Application', {
      vpc: network.vpc,
      dbInstance: database.dbInstance,
      dbSecret: database.dbSecret,
      mediawikiSecurityGroup: network.mediawikiSecurityGroup,
    });
  }
}
