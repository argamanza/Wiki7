import { Construct } from 'constructs';
import * as cloudfront from 'aws-cdk-lib/aws-cloudfront';
import * as origins from 'aws-cdk-lib/aws-cloudfront-origins';
import * as route53 from 'aws-cdk-lib/aws-route53';
import * as targets from 'aws-cdk-lib/aws-route53-targets';
import * as acm from 'aws-cdk-lib/aws-certificatemanager';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as autoscaling from 'aws-cdk-lib/aws-autoscaling';
import * as cdk from 'aws-cdk-lib';

export interface CloudFrontProps {
  autoScalingGroup: autoscaling.AutoScalingGroup;
  hostedZone: route53.IHostedZone;
  certificate: acm.ICertificate;
  domainName: string;
  mediawikiStorageBucket: s3.Bucket;
  /** Enable CloudFront access logging (free, stored in S3) */
  enableAccessLogging?: boolean;
}

export class CloudFrontConstruct extends Construct {
  readonly distribution: cloudfront.Distribution;

  constructor(scope: Construct, id: string, props: CloudFrontProps) {
    super(scope, id);

    const {
      autoScalingGroup,
      hostedZone,
      certificate,
      domainName,
      mediawikiStorageBucket,
      enableAccessLogging,
    } = props;

    // EC2 origin - CloudFront connects directly to EC2 public IP via HTTP
    // We use the ASG's first instance. In production, you'd use an Elastic IP
    // or a simple origin with the instance's public DNS.
    // For now, we create an HttpOrigin that will be configured post-deploy.
    const ec2Origin = new origins.HttpOrigin(
      `origin.${domainName}`,
      {
        protocolPolicy: cloudfront.OriginProtocolPolicy.HTTP_ONLY,
        httpPort: 80,
        connectionTimeout: cdk.Duration.seconds(10),
        connectionAttempts: 3,
        customHeaders: {
          'X-Origin-Verify': 'wiki7-cloudfront-secret',
        },
      }
    );

    // S3 Origin with OAC for static assets
    const s3Origin = origins.S3BucketOrigin.withOriginAccessControl(
      mediawikiStorageBucket,
      {
        originAccessLevels: [
          cloudfront.AccessLevel.READ,
          cloudfront.AccessLevel.LIST,
        ],
      }
    );

    // Redirect www to apex domain
    const redirectFunction = new cloudfront.Function(
      this,
      'RedirectWwwToApexFunction',
      {
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
      }
    );

    // Security Headers Policy
    const responseHeadersPolicy = new cloudfront.ResponseHeadersPolicy(
      this,
      'SecurityHeadersPolicy',
      {
        responseHeadersPolicyName: 'Wiki7SecurityHeaders',
        comment: 'Security headers for Wiki7',
        securityHeadersBehavior: {
          contentTypeOptions: { override: true },
          frameOptions: {
            frameOption: cloudfront.HeadersFrameOption.DENY,
            override: true,
          },
          xssProtection: {
            protection: true,
            modeBlock: true,
            override: true,
          },
          strictTransportSecurity: {
            accessControlMaxAge: cdk.Duration.days(365),
            includeSubdomains: true,
            override: true,
          },
        },
      }
    );

    // Cache policy for static content (images, assets)
    const staticContentCachePolicy = new cloudfront.CachePolicy(
      this,
      'StaticContentCachePolicy',
      {
        cachePolicyName: 'Wiki7StaticContent',
        comment: 'Cache policy for Wiki7 static content',
        defaultTtl: cdk.Duration.days(7),
        minTtl: cdk.Duration.days(1),
        maxTtl: cdk.Duration.days(30),
        enableAcceptEncodingGzip: true,
        enableAcceptEncodingBrotli: true,
        headerBehavior: cloudfront.CacheHeaderBehavior.allowList(
          'Origin',
          'Access-Control-Request-Method',
          'Access-Control-Request-Headers'
        ),
        queryStringBehavior: cloudfront.CacheQueryStringBehavior.none(),
        cookieBehavior: cloudfront.CacheCookieBehavior.none(),
      }
    );

    // Access logging bucket (optional, free for CloudFront logs)
    let logBucket: s3.Bucket | undefined;
    if (enableAccessLogging) {
      logBucket = new s3.Bucket(this, 'Wiki7AccessLogsBucket', {
        bucketName: 'wiki7-cloudfront-logs',
        encryption: s3.BucketEncryption.S3_MANAGED,
        blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
        lifecycleRules: [
          {
            id: 'ExpireOldLogs',
            enabled: true,
            expiration: cdk.Duration.days(30),
          },
        ],
        removalPolicy: cdk.RemovalPolicy.DESTROY,
        autoDeleteObjects: true,
        objectOwnership: s3.ObjectOwnership.BUCKET_OWNER_PREFERRED,
      });
    }

    // Create CloudFront distribution (no separate WAF - uses CloudFront's built-in protections)
    this.distribution = new cloudfront.Distribution(
      this,
      'Wiki7Distribution',
      {
        defaultBehavior: {
          origin: ec2Origin,
          viewerProtocolPolicy:
            cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
          allowedMethods: cloudfront.AllowedMethods.ALLOW_ALL,
          cachePolicy: cloudfront.CachePolicy.CACHING_DISABLED,
          originRequestPolicy: cloudfront.OriginRequestPolicy.ALL_VIEWER,
          responseHeadersPolicy,
          functionAssociations: [
            {
              function: redirectFunction,
              eventType: cloudfront.FunctionEventType.VIEWER_REQUEST,
            },
          ],
        },
        additionalBehaviors: {
          'images/*': {
            origin: s3Origin,
            viewerProtocolPolicy:
              cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            allowedMethods: cloudfront.AllowedMethods.ALLOW_GET_HEAD,
            cachePolicy: staticContentCachePolicy,
            responseHeadersPolicy,
            compress: true,
          },
          'assets/*': {
            origin: s3Origin,
            viewerProtocolPolicy:
              cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            allowedMethods: cloudfront.AllowedMethods.ALLOW_GET_HEAD,
            cachePolicy: staticContentCachePolicy,
            responseHeadersPolicy,
            compress: true,
          },
        },
        domainNames: [domainName, `www.${domainName}`],
        certificate,
        // No separate WAF stack - CloudFront provides basic protection
        // including geo-restriction and rate limiting via CloudFront Functions
        enableLogging: enableAccessLogging,
        logBucket,
        priceClass: cloudfront.PriceClass.PRICE_CLASS_100,
      }
    );

    // DNS records
    new route53.ARecord(this, 'Wiki7ApexAlias', {
      zone: hostedZone,
      recordName: '',
      target: route53.RecordTarget.fromAlias(
        new targets.CloudFrontTarget(this.distribution)
      ),
    });

    new route53.ARecord(this, 'Wiki7WwwAlias', {
      zone: hostedZone,
      recordName: 'www',
      target: route53.RecordTarget.fromAlias(
        new targets.CloudFrontTarget(this.distribution)
      ),
    });

    // Tags
    cdk.Tags.of(this).add('Project', 'Wiki7');
    cdk.Tags.of(this).add('Component', 'CDN');

    // Outputs
    new cdk.CfnOutput(this, 'DistributionId', {
      value: this.distribution.distributionId,
      description: 'CloudFront Distribution ID',
    });

    new cdk.CfnOutput(this, 'DistributionDomainName', {
      value: this.distribution.distributionDomainName,
      description: 'CloudFront Distribution Domain Name',
    });
  }
}
