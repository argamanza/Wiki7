#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { Wiki7DnsStack } from '../lib/wiki7-dns-stack';
import { Wiki7CertificateStack } from '../lib/wiki7-certificate-stack';
import { Wiki7WafStack } from '../lib/wiki7-waf-stack';
import { Wiki7CdkStack } from '../lib/wiki7-cdk-stack';

const app = new cdk.App();

const account = process.env.CDK_DEFAULT_ACCOUNT;

new Wiki7DnsStack(app, 'Wiki7DnsStack', {
  env: { account, region: 'il-central-1' },
  domainName: 'wiki7.co.il',
});

new Wiki7CertificateStack(app, 'Wiki7CertificateStack', {
  env: { account, region: 'us-east-1' },
  domainName: 'wiki7.co.il',
});

new Wiki7WafStack(app, 'Wiki7WafStack', {
  env: { account, region: 'us-east-1' },
});

new Wiki7CdkStack(app, 'Wiki7CdkStack', {
  env: { account, region: 'il-central-1' },
});
