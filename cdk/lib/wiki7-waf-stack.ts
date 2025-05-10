import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as wafv2 from 'aws-cdk-lib/aws-wafv2';
import {CrossRegionSsmSync} from "./cross-region-ssm-sync";
import * as ssm from "aws-cdk-lib/aws-ssm";
import * as logs from 'aws-cdk-lib/aws-logs';

interface Wiki7WafStackProps extends cdk.StackProps {
}

export class Wiki7WafStack extends cdk.Stack {
  readonly webAcl: wafv2.CfnWebACL;

  constructor(scope: Construct, id: string, props: Wiki7WafStackProps) {
    super(scope, id, {
      ...props,
      env: {
        region: 'us-east-1',
        account: props.env?.account,
      },
    });

    // Create WAF Web ACL
    this.webAcl = new wafv2.CfnWebACL(this, 'Wiki7WebAcl', {
      defaultAction: { allow: {} },
      scope: 'CLOUDFRONT',
      visibilityConfig: {
        sampledRequestsEnabled: true,
        cloudWatchMetricsEnabled: true,
        metricName: 'Wiki7WebAcl',
      },
      description: 'WAF for Wiki7 MediaWiki site',
      rules: [
        // Block requests from certain countries
        {
          name: 'BlockCertainCountries',
          priority: 1,
          statement: {
            geoMatchStatement: {
              countryCodes: [
                'AF', // Afghanistan
                'DZ', // Algeria
                'BD', // Bangladesh
                'BY', // Belarus
                'CN', // China
                'CU', // Cuba
                'IR', // Iran
                'IQ', // Iraq
                'KP', // North Korea
                'LB', // Lebanon
                'LY', // Libya
                'PK', // Pakistan
                'RU', // Russia
                'SY', // Syria
                'YE', // Yemen
                'VE', // Venezuela
                'VN', // Vietnam
              ]
            },
          },
          action: { block: {} },
          visibilityConfig: {
            cloudWatchMetricsEnabled: true,
            metricName: 'GeoBlock',
            sampledRequestsEnabled: true,
          },
        },
        // AWS Managed Rules - Core rule set
        {
          name: 'AWS-AWSManagedRulesCommonRuleSet',
          priority: 2,
          overrideAction: { none: {} },
          statement: {
            managedRuleGroupStatement: {
              vendorName: 'AWS',
              name: 'AWSManagedRulesCommonRuleSet',
              excludedRules: [
                { name: 'SizeRestrictions_BODY' }, // MediaWiki can have large POST bodies
                { name: 'SizeRestrictions_QUERYSTRING' }, // Long query strings for searches
                { name: 'CrossSiteScripting_BODY' }, // XSS rule for body (blocked image uploads)
              ],
            },
          },
          visibilityConfig: {
            sampledRequestsEnabled: true,
            cloudWatchMetricsEnabled: true,
            metricName: 'AWS-AWSManagedRulesCommonRuleSet',
          },
        },
        // AWS Managed Rules - Known bad inputs
        {
          name: 'AWS-AWSManagedRulesKnownBadInputsRuleSet',
          priority: 3,
          overrideAction: { none: {} },
          statement: {
            managedRuleGroupStatement: {
              vendorName: 'AWS',
              name: 'AWSManagedRulesKnownBadInputsRuleSet',
            },
          },
          visibilityConfig: {
            sampledRequestsEnabled: true,
            cloudWatchMetricsEnabled: true,
            metricName: 'AWS-AWSManagedRulesKnownBadInputsRuleSet',
          },
        },
        // AWS Managed Rules - SQL injection
        {
          name: 'AWS-AWSManagedRulesSQLiRuleSet',
          priority: 4,
          overrideAction: { none: {} },
          statement: {
            managedRuleGroupStatement: {
              vendorName: 'AWS',
              name: 'AWSManagedRulesSQLiRuleSet',
            },
          },
          visibilityConfig: {
            sampledRequestsEnabled: true,
            cloudWatchMetricsEnabled: true,
            metricName: 'AWS-AWSManagedRulesSQLiRuleSet',
          },
        },
        // AWS Managed Rules - Linux specific
        {
          name: 'AWS-AWSManagedRulesLinuxRuleSet',
          priority: 5,
          overrideAction: { none: {} },
          statement: {
            managedRuleGroupStatement: {
              vendorName: 'AWS',
              name: 'AWSManagedRulesLinuxRuleSet',
            },
          },
          visibilityConfig: {
            sampledRequestsEnabled: true,
            cloudWatchMetricsEnabled: true,
            metricName: 'AWS-AWSManagedRulesLinuxRuleSet',
          },
        },
        // AWS Managed Rules - PHP application specific
        {
          name: 'AWS-AWSManagedRulesPHPRuleSet',
          priority: 6,
          overrideAction: { none: {} },
          statement: {
            managedRuleGroupStatement: {
              vendorName: 'AWS',
              name: 'AWSManagedRulesPHPRuleSet',
            },
          },
          visibilityConfig: {
            sampledRequestsEnabled: true,
            cloudWatchMetricsEnabled: true,
            metricName: 'AWS-AWSManagedRulesPHPRuleSet',
          },
        },
        // Rate limiting - 2000 requests per 5 minutes per IP
        {
          name: 'RateLimitPerIP',
          priority: 7,
          action: { block: {} },
          statement: {
            rateBasedStatement: {
              limit: 2000,
              aggregateKeyType: 'IP',
            },
          },
          visibilityConfig: {
            sampledRequestsEnabled: true,
            cloudWatchMetricsEnabled: true,
            metricName: 'RateLimitPerIP',
          },
        },
        // Custom rule - Block suspicious MediaWiki patterns
        {
          name: 'BlockSuspiciousMediaWikiPatterns',
          priority: 8,
          action: { block: {} },
          statement: {
            orStatement: {
              statements: [
                // Block requests with multiple dots in URI (potential directory traversal)
                {
                  byteMatchStatement: {
                    searchString: '..',
                    fieldToMatch: { uriPath: {} },
                    textTransformations: [{ priority: 0, type: 'URL_DECODE' }],
                    positionalConstraint: 'CONTAINS',
                  },
                },
                // Block automated spam patterns in User-Agent
                {
                  regexMatchStatement: {
                    regexString: '.*(bot|crawl|spider|scan).*',
                    fieldToMatch: { singleHeader: { name: 'User-Agent' } },
                    textTransformations: [{ priority: 0, type: 'LOWERCASE' }],
                  },
                },
              ],
            },
          },
          visibilityConfig: {
            sampledRequestsEnabled: true,
            cloudWatchMetricsEnabled: true,
            metricName: 'BlockSuspiciousMediaWikiPatterns',
          },
        },
        // Allow legitimate bots (Google, Bing, etc.) - higher priority than block rule
        {
          name: 'AllowLegitimateBot',
          priority: 9,
          action: { allow: {} },
          statement: {
            orStatement: {
              statements: [
                {
                  byteMatchStatement: {
                    searchString: 'googlebot',
                    fieldToMatch: { singleHeader: { name: 'User-Agent' } },
                    textTransformations: [{ priority: 0, type: 'LOWERCASE' }],
                    positionalConstraint: 'CONTAINS',
                  },
                },
                {
                  byteMatchStatement: {
                    searchString: 'bingbot',
                    fieldToMatch: { singleHeader: { name: 'User-Agent' } },
                    textTransformations: [{ priority: 0, type: 'LOWERCASE' }],
                    positionalConstraint: 'CONTAINS',
                  },
                },
              ],
            },
          },
          visibilityConfig: {
            sampledRequestsEnabled: true,
            cloudWatchMetricsEnabled: true,
            metricName: 'AllowLegitimateBot',
          },
        },
      ],
    });

    // Create the log group
    const wafLogGroup = new logs.LogGroup(this, 'WafLogGroup', {
      logGroupName: 'aws-waf-logs-wiki7',
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

// Define the logging configuration
    new wafv2.CfnLoggingConfiguration(this, 'Wiki7WafLogging', {
      resourceArn: this.webAcl.attrArn,
      logDestinationConfigs: [
        cdk.Stack.of(this).formatArn({
          service: 'logs',
          region: 'us-east-1',
          account: cdk.Stack.of(this).account,
          resource: 'log-group',
          resourceName: wafLogGroup.logGroupName,
          arnFormat: cdk.ArnFormat.COLON_RESOURCE_NAME,
        }),
      ],
      // Directly specify the loggingFilter property with correct casing
      loggingFilter: {
        DefaultBehavior: 'DROP',
        Filters: [
          {
            Behavior: 'KEEP',
            Requirement: 'MEETS_ALL',
            Conditions: [
              {
                ActionCondition: {
                  Action: 'BLOCK',
                },
              },
            ],
          },
        ],
      },
    });

    new ssm.StringParameter(this, 'Wiki7CertificateArnParameter', {
      parameterName: '/wiki7/waf-webacl/arn',
      stringValue: this.webAcl.attrArn,
    });

    new CrossRegionSsmSync(this, 'WafSync', {
      parameterName: '/wiki7/waf-webacl/arn',
      sourceRegion: 'us-east-1',
      targetRegion: 'il-central-1',
    });

  }
}