import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as acm from 'aws-cdk-lib/aws-certificatemanager';
import * as route53 from 'aws-cdk-lib/aws-route53';
import { NetworkStack } from './network-stack';
import { DatabaseStack } from './database-stack';
import { BackupStack } from './backup-stack';
import { ApplicationStack } from './application-stack';

export class Wiki7CdkStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const hostedZone = route53.HostedZone.fromHostedZoneAttributes(this, 'ImportedZone', {
      hostedZoneId: cdk.Fn.importValue('Wiki7HostedZoneId'),
      zoneName: cdk.Fn.importValue('Wiki7HostedZoneName'),
    });

    const certificateArn = cdk.Fn.importValue('Wiki7CertificateArn');
    const certificate = acm.Certificate.fromCertificateArn(this, 'Wiki7Certificate', certificateArn);

    const network = new NetworkStack(this, 'Network');

    const database = new DatabaseStack(this, 'Database', {
      vpc: network.vpc,
      mediawikiSecurityGroup: network.mediawikiSecurityGroup,
    });

    new BackupStack(this, 'Backup', {
      dbInstance: database.dbInstance,
    });

    new ApplicationStack(this, 'Application', {
      vpc: network.vpc,
      dbInstance: database.dbInstance,
      dbSecret: database.dbSecret,
      mediawikiSecurityGroup: network.mediawikiSecurityGroup,
    });

    // Later: pass `certificate` and `hostedZone` to a CloudFrontStack if needed
  }
}
