import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as acm from 'aws-cdk-lib/aws-certificatemanager';
import * as route53 from 'aws-cdk-lib/aws-route53';
import { NetworkStack } from './network-stack';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import { DatabaseStack } from './database-stack';
import { BackupStack } from './backup-stack';
import { ApplicationStack } from './application-stack';
import { CloudFrontConstruct } from './cloudfront-stack';

export class Wiki7CdkStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    
    const hostedZoneId = ssm.StringParameter.valueForStringParameter(this, '/wiki7/hostedzone/id');
    const hostedZoneName = ssm.StringParameter.valueForStringParameter(this, '/wiki7/hostedzone/name');

    const hostedZone = route53.HostedZone.fromHostedZoneAttributes(this, 'ImportedZone', {
      hostedZoneId,
      zoneName: hostedZoneName,
    });

    const certificateArn = ssm.StringParameter.valueForStringParameter(this, '/wiki7/certificate/arn');
    const certificate = acm.Certificate.fromCertificateArn(this, 'Wiki7Certificate', certificateArn);

    const network = new NetworkStack(this, 'Network');

    const database = new DatabaseStack(this, 'Database', {
      vpc: network.vpc,
      mediawikiSecurityGroup: network.mediawikiSecurityGroup,
    });

    new BackupStack(this, 'Backup', {
      dbInstance: database.dbInstance,
    });

    const app = new ApplicationStack(this, 'Application', {
      vpc: network.vpc,
      dbInstance: database.dbInstance,
      dbSecret: database.dbSecret,
      mediawikiSecurityGroup: network.mediawikiSecurityGroup,
    });

    new CloudFrontConstruct(this, 'CloudFront', {
      alb: app.alb,
      hostedZone: hostedZone,
      certificate: certificate,
      domainName: 'wiki7.co.il',
    });
  }
}
