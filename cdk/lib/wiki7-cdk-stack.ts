import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { NetworkStack } from './network-stack'
import { DatabaseStack } from './database-stack';
import { ApplicationStack } from './application-stack';

export class Wiki7CdkStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Provision networking resources (VPC and SGs)
    const network = new NetworkStack(this, 'Network');

    // Provision RDS database and secrets
    const database = new DatabaseStack(this, 'Database', {
      vpc: network.vpc,
      mediawikiSecurityGroup: network.mediawikiSecurityGroup,
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
