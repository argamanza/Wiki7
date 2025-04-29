import { Construct } from 'constructs';
import * as cdk from 'aws-cdk-lib';
import * as cloudfront from 'aws-cdk-lib/aws-cloudfront';
import * as origins from 'aws-cdk-lib/aws-cloudfront-origins';
import * as route53 from 'aws-cdk-lib/aws-route53';
import * as targets from 'aws-cdk-lib/aws-route53-targets';
import * as elbv2 from 'aws-cdk-lib/aws-elasticloadbalancingv2';
import * as acm from 'aws-cdk-lib/aws-certificatemanager';

interface CloudFrontProps {
  alb: elbv2.ApplicationLoadBalancer;
  hostedZone: route53.IHostedZone;
  certificate: acm.ICertificate;
  domainName: string;
}

export class CloudFrontConstruct extends Construct {
  constructor(scope: Construct, id: string, props: CloudFrontProps) {
    super(scope, id);

    const { alb, hostedZone, certificate, domainName } = props;

    const albOrigin = new origins.LoadBalancerV2Origin(alb, {
      protocolPolicy: cloudfront.OriginProtocolPolicy.HTTP_ONLY,
    });

    const distribution = new cloudfront.Distribution(this, 'Wiki7Distribution', {
      defaultBehavior: {
        origin: albOrigin,
        viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        allowedMethods: cloudfront.AllowedMethods.ALLOW_ALL,
        cachePolicy: cloudfront.CachePolicy.CACHING_DISABLED,
        originRequestPolicy: cloudfront.OriginRequestPolicy.ALL_VIEWER,
      },
      domainNames: [domainName],
      certificate,
    });

    new route53.ARecord(this, 'Wiki7ApexAlias', {
      zone: hostedZone,
      recordName: '',
      target: route53.RecordTarget.fromAlias(new targets.CloudFrontTarget(distribution)),
    });
  }
}
