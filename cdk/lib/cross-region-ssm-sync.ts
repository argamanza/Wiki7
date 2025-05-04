import { Construct } from 'constructs';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as path from 'path';
import * as cr from 'aws-cdk-lib/custom-resources';
import * as cdk from 'aws-cdk-lib';

interface CrossRegionSsmSyncProps {
    parameterName: string;
    sourceRegion: string;
    targetRegion: string;
}

export class CrossRegionSsmSync extends Construct {
    constructor(scope: Construct, id: string, props: CrossRegionSsmSyncProps) {
        super(scope, id);

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
                `arn:aws:ssm:${props.sourceRegion}:${cdk.Aws.ACCOUNT_ID}:parameter${props.parameterName}`,
                `arn:aws:ssm:${props.targetRegion}:${cdk.Aws.ACCOUNT_ID}:parameter${props.parameterName}`,
            ],
        }));

        // Lambda function to sync SSM parameter
        const ssmSyncFunction = new lambda.Function(this, 'SSMSyncLambda', {
            runtime: lambda.Runtime.PYTHON_3_11,
            handler: 'ssm_sync.lambda_handler',
            code: lambda.Code.fromAsset(path.join(__dirname, '../lambda/ssm-sync')),
            environment: {
                TARGET_REGION: props.targetRegion,
                PARAMETER_NAME: props.parameterName,
            },
            role: syncRole,
            timeout: cdk.Duration.seconds(30),
        });

        new cr.AwsCustomResource(this, 'InvokeSSMSyncLambda', {
            onCreate: {
                service: 'Lambda',
                action: 'invoke',
                parameters: {
                    FunctionName: ssmSyncFunction.functionName,
                    InvocationType: 'Event',
                },
                physicalResourceId: cr.PhysicalResourceId.of(`${id}-InvokeSSMSyncLambdaResource`),
            },
            onUpdate: {
                service: 'Lambda',
                action: 'invoke',
                parameters: {
                    FunctionName: ssmSyncFunction.functionName,
                    InvocationType: 'Event',
                },
                physicalResourceId: cr.PhysicalResourceId.of(`${id}-InvokeSSMSyncLambdaResource`),
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