import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as acm from 'aws-cdk-lib/aws-certificatemanager';
import * as route53 from 'aws-cdk-lib/aws-route53';

interface Wiki7CertificateStackProps extends cdk.StackProps {
  domainName: string;
}

export class Wiki7CertificateStack extends cdk.Stack {
  readonly certificate: acm.Certificate;

  constructor(scope: Construct, id: string, props: Wiki7CertificateStackProps) {
    super(scope, id, {
      ...props,
      env: {
        region: 'us-east-1',
        account: props.env?.account,
      },
    });

    const hostedZone = route53.HostedZone.fromLookup(this, 'HostedZone', {
      domainName: props.domainName,
    });
    

    this.certificate = new acm.Certificate(this, 'Wiki7Certificate', {
      domainName: props.domainName,
      validation: acm.CertificateValidation.fromDns(hostedZone),
    });

    new cdk.CfnOutput(this, 'Wiki7CertificateArnExport', {
      value: this.certificate.certificateArn,
      exportName: 'Wiki7CertificateArn',
    });
  }
}
