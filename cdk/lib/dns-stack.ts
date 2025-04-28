import { Construct } from 'constructs';
import * as route53 from 'aws-cdk-lib/aws-route53';
import * as cdk from 'aws-cdk-lib';

interface DnsStackProps {
  domainName: string;
}

export class DnsStack extends Construct {
  readonly hostedZone: route53.IHostedZone;

  constructor(scope: Construct, id: string, props: DnsStackProps) {
    super(scope, id);

    const { domainName } = props;

    this.hostedZone = new route53.HostedZone(this, 'Wiki7HostedZone', {
      zoneName: domainName,
      comment: 'Hosted zone for Wiki7.co.il',
    });

    new cdk.CfnOutput(this, 'HostedZoneId', {
      value: this.hostedZone.hostedZoneId,
    });

    new cdk.CfnOutput(this, 'NameServers', {
      value: cdk.Fn.join(', ', this.hostedZone.hostedZoneNameServers!),
    });
  }
}
