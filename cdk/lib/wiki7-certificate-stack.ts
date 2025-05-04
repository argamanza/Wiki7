import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as acm from 'aws-cdk-lib/aws-certificatemanager';
import * as route53 from 'aws-cdk-lib/aws-route53';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda'
import * as path from 'path';
import * as cr from 'aws-cdk-lib/custom-resources';
import {CrossRegionSsmSync} from "./cross-region-ssm-sync";

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
      domainName: props.domainName,  // 'wiki7.co.il'
      subjectAlternativeNames: [`www.${props.domainName}`], // 'www.wiki7.co.il'
      validation: acm.CertificateValidation.fromDns(hostedZone),
    });    

    new ssm.StringParameter(this, 'Wiki7CertificateArnParameter', {
      parameterName: '/wiki7/certificate/arn',
      stringValue: this.certificate.certificateArn,
    });

    new CrossRegionSsmSync(this, 'CertificateSync', {
      parameterName: '/wiki7/certificate/arn',
      sourceRegion: 'us-east-1',
      targetRegion: 'il-central-1',
    });
    
  }
}
