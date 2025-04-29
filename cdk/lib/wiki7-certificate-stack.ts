import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as acm from 'aws-cdk-lib/aws-certificatemanager';
import * as route53 from 'aws-cdk-lib/aws-route53';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda'
import * as path from 'path';
import * as cr from 'aws-cdk-lib/custom-resources';

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

    // IAM Role for the Lambda
    const syncRole = new iam.Role(this, 'SSMSyncRole', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
    });

    syncRole.addManagedPolicy(iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'));

    syncRole.addToPolicy(new iam.PolicyStatement({
      actions: [
        'ssm:GetParameter',
        'ssm:PutParameter',
      ],
      resources: [
        `arn:aws:ssm:${this.region}:${this.account}:parameter/wiki7/certificate/arn`,
        `arn:aws:ssm:il-central-1:${this.account}:parameter/wiki7/certificate/arn`,
      ],
    }));

    // Lambda function to sync SSM parameter
    const ssmSyncFunction = new lambda.Function(this, 'SSMSyncLambda', {
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'ssm_sync.lambda_handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../lambda/ssm-sync')), // We'll create the code soon
      environment: {
        TARGET_REGION: 'il-central-1',
        PARAMETER_NAME: '/wiki7/certificate/arn',
      },
      role: syncRole,
      timeout: cdk.Duration.seconds(30),
    });

    new cdk.CfnOutput(this, 'SSMSyncLambdaFunctionName', {
      value: ssmSyncFunction.functionName,
      description: 'Name of the SSM sync Lambda function',
    });

    new cr.AwsCustomResource(this, 'InvokeSSMSyncLambda', {
      onCreate: {
        service: 'Lambda',
        action: 'invoke',
        parameters: {
          FunctionName: ssmSyncFunction.functionName,
          InvocationType: 'Event',
        },
        physicalResourceId: cr.PhysicalResourceId.of('InvokeSSMSyncLambdaResource'),
      },
      onUpdate: {
        service: 'Lambda',
        action: 'invoke',
        parameters: {
          FunctionName: ssmSyncFunction.functionName,
          InvocationType: 'Event',
        },
        physicalResourceId: cr.PhysicalResourceId.of('InvokeSSMSyncLambdaResource'),
      },
      policy: cr.AwsCustomResourcePolicy.fromStatements([
        new iam.PolicyStatement({
          actions: ['lambda:InvokeFunction'],
          resources: [ssmSyncFunction.functionArn],
          effect: iam.Effect.ALLOW,
        }),
      ]),
    });
    
  }
}
