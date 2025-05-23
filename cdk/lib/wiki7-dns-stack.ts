import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as route53 from 'aws-cdk-lib/aws-route53';
import * as ssm from 'aws-cdk-lib/aws-ssm';

interface Wiki7DnsStackProps extends cdk.StackProps {
  domainName: string;
}

export class Wiki7DnsStack extends cdk.Stack {
  readonly hostedZone: route53.HostedZone;

  constructor(scope: Construct, id: string, props: Wiki7DnsStackProps) {
    super(scope, id, props);

    this.hostedZone = new route53.HostedZone(this, 'Wiki7HostedZone', {
      zoneName: props.domainName,
      comment: 'Hosted zone for Wiki7.co.il',
    });

    new ssm.StringParameter(this, 'Wiki7HostedZoneIdParameter', {
      parameterName: '/wiki7/hostedzone/id',
      stringValue: this.hostedZone.hostedZoneId,
    });

    new ssm.StringParameter(this, 'Wiki7HostedZoneNameParameter', {
      parameterName: '/wiki7/hostedzone/name',
      stringValue: this.hostedZone.zoneName,
    });

    new cdk.CfnOutput(this, 'NameServers', {
      value: cdk.Fn.join(', ', this.hostedZone.hostedZoneNameServers!),
      description: 'NS records to copy to domain registrar',
    });
  }
}
