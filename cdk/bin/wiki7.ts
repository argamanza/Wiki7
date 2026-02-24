#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { Wiki7DnsStack } from '../lib/wiki7-dns-stack';
import { Wiki7CertificateStack } from '../lib/wiki7-certificate-stack';
import { Wiki7CdkStack } from '../lib/wiki7-cdk-stack';

const app = new cdk.App();

// Parameterized configuration (no more hardcoded domain)
const domainName = app.node.tryGetContext('domainName') || 'wiki7.co.il';
const account = process.env.CDK_DEFAULT_ACCOUNT;
const primaryRegion = app.node.tryGetContext('primaryRegion') || 'il-central-1';

// Feature flags for cost control
const enableRds = app.node.tryGetContext('enableRds') === 'true';
const enableMultiAz = app.node.tryGetContext('enableMultiAz') === 'true';
const enablePrivateSubnets = app.node.tryGetContext('enablePrivateSubnets') === 'true';
const alertEmail = app.node.tryGetContext('alertEmail') || undefined;
const keyPairName = app.node.tryGetContext('keyPairName') || undefined;

// DNS Stack (Route 53 hosted zone)
new Wiki7DnsStack(app, 'Wiki7DnsStack', {
  env: { account, region: primaryRegion },
  domainName,
});

// Certificate Stack (must be in us-east-1 for CloudFront)
new Wiki7CertificateStack(app, 'Wiki7CertificateStack', {
  env: { account, region: 'us-east-1' },
  domainName,
});

// WAF stack removed - CloudFront provides built-in protection (saves ~$15/mo)

// Main Infrastructure Stack
new Wiki7CdkStack(app, 'Wiki7CdkStack', {
  env: { account, region: primaryRegion },
  domainName,
  enableRds,
  enableMultiAz,
  enablePrivateSubnets,
  alertEmail,
  keyPairName,
});
