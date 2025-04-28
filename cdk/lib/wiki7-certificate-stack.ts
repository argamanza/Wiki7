import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as acm from 'aws-cdk-lib/aws-certificatemanager';
import * as route53 from 'aws-cdk-lib/aws-route53';

interface Wiki7CertificateStackProps extends cdk.StackProps {
  domainName: string;
  hostedZone: route53.IHostedZone;
}

export class Wiki7CertificateStack extends cdk.Stack {
  readonly certificate: acm.Certificate;

  constructor(scope: Construct, id: string, props: Wiki7CertificateStackProps) {
    super(scope, id, {
      ...props,
      env: {
        region: 'us-east-1', // Force us-east-1 region
        account: props.env?.account, // Keep the same AWS account
      },
      crossRegionReferences: true,
    });

    this.certificate = new acm.Certificate(this, 'Wiki7Certificate', {
      domainName: props.domainName,
      validation: acm.CertificateValidation.fromDns(props.hostedZone),
    });
  }
}
