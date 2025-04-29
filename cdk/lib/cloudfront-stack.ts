import { Construct } from 'constructs';
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

    const redirectFunction = new cloudfront.Function(this, 'RedirectWwwToApexFunction', {
      code: cloudfront.FunctionCode.fromInline(`
        function handler(event) {
          var request = event.request;
          var host = request.headers.host.value;
          if (host.startsWith('www.')) {
            var redirect = 'https://' + host.substring(4) + request.uri;
            return {
              statusCode: 301,
              statusDescription: 'Moved Permanently',
              headers: {
                location: { value: redirect }
              }
            };
          }
          return request;
        }
      `),
    });    

    const distribution = new cloudfront.Distribution(this, 'Wiki7Distribution', {
      defaultBehavior: {
        origin: albOrigin,
        viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        allowedMethods: cloudfront.AllowedMethods.ALLOW_ALL,
        cachePolicy: cloudfront.CachePolicy.CACHING_DISABLED,
        originRequestPolicy: cloudfront.OriginRequestPolicy.ALL_VIEWER,
        functionAssociations: [
          {
            function: redirectFunction,
            eventType: cloudfront.FunctionEventType.VIEWER_REQUEST,
          },
        ],
      },
      domainNames: [props.domainName, `www.${props.domainName}`],
      certificate,
    });

    new route53.ARecord(this, 'Wiki7ApexAlias', {
      zone: hostedZone,
      recordName: '',
      target: route53.RecordTarget.fromAlias(new targets.CloudFrontTarget(distribution)),
    });

    new route53.ARecord(this, 'Wiki7WwwAlias', {
      zone: props.hostedZone,
      recordName: `www`,
      target: route53.RecordTarget.fromAlias(new targets.CloudFrontTarget(distribution)),
    });
  }
}
