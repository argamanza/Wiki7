import { Construct } from 'constructs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as autoscaling from 'aws-cdk-lib/aws-autoscaling';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as cr from 'aws-cdk-lib/custom-resources';
import * as cdk from 'aws-cdk-lib';
import * as path from 'path';

export interface ApplicationStackProps {
  vpc: ec2.Vpc;
  ec2SecurityGroup: ec2.SecurityGroup;
  domainName: string;
  /** SSH key pair name for EC2 access (optional) */
  keyPairName?: string;
}

export class ApplicationStack extends Construct {
  readonly autoScalingGroup: autoscaling.AutoScalingGroup;
  readonly mediawikiStorageBucket: s3.Bucket;

  constructor(scope: Construct, id: string, props: ApplicationStackProps) {
    super(scope, id);

    const { vpc, ec2SecurityGroup, domainName } = props;

    // Create S3 bucket for MediaWiki storage (images, assets)
    this.mediawikiStorageBucket = new s3.Bucket(this, 'Wiki7StorageBucket', {
      bucketName: 'wiki7-storage',
      encryption: s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      versioned: true,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      cors: [
        {
          allowedMethods: [s3.HttpMethods.GET, s3.HttpMethods.HEAD],
          allowedOrigins: [
            `https://${domainName}`,
            `https://www.${domainName}`,
          ],
          allowedHeaders: ['Content-Type', 'Authorization', 'Content-Length'],
          maxAge: 3000,
        },
      ],
      lifecycleRules: [
        {
          id: 'ExpireOldVersions',
          enabled: true,
          noncurrentVersionExpiration: cdk.Duration.days(7),
          expiredObjectDeleteMarker: true,
        },
      ],
    });

    // IAM Role for EC2 instances
    const ec2Role = new iam.Role(this, 'Wiki7EC2Role', {
      assumedBy: new iam.ServicePrincipal('ec2.amazonaws.com'),
      description: 'IAM role for Wiki7 MediaWiki EC2 instances',
      managedPolicies: [
        // SSM for remote management (no need for SSH bastion)
        iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonSSMManagedInstanceCore'),
        // CloudWatch agent for metrics
        iam.ManagedPolicy.fromAwsManagedPolicyName('CloudWatchAgentServerPolicy'),
      ],
    });

    // Grant S3 access to EC2 role
    this.mediawikiStorageBucket.grantReadWrite(ec2Role);

    // Explicit S3 permissions for MediaWiki AWS extension
    ec2Role.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          's3:PutObject',
          's3:PutObjectAcl',
          's3:GetObject',
          's3:DeleteObject',
          's3:ListBucket',
          's3:GetBucketLocation',
        ],
        resources: [
          this.mediawikiStorageBucket.bucketArn,
          `${this.mediawikiStorageBucket.bucketArn}/*`,
        ],
      })
    );

    // User data script to bootstrap MediaWiki on EC2
    const userData = ec2.UserData.forLinux();
    userData.addCommands(
      '#!/bin/bash',
      'set -euo pipefail',
      '',
      '# Log all output for debugging',
      'exec > >(tee /var/log/user-data.log) 2>&1',
      '',
      '# Update system',
      'dnf update -y',
      '',
      '# Install required packages',
      'dnf install -y nginx php8.2-fpm php8.2-mysqlnd php8.2-xml php8.2-intl php8.2-gd php8.2-mbstring php8.2-json php8.2-opcache mariadb114-server mariadb114 aws-cli',
      '',
      '# Enable and start MariaDB',
      'systemctl enable mariadb',
      'systemctl start mariadb',
      '',
      '# Enable and start PHP-FPM',
      'systemctl enable php-fpm',
      'systemctl start php-fpm',
      '',
      '# Enable and start Nginx',
      'systemctl enable nginx',
      'systemctl start nginx',
      '',
      '# Install CloudWatch agent',
      'dnf install -y amazon-cloudwatch-agent',
      'systemctl enable amazon-cloudwatch-agent',
      'systemctl start amazon-cloudwatch-agent',
      '',
      '# Signal successful initialization',
      'echo "Wiki7 EC2 initialization complete"',
    );

    // Launch template with key pair support
    const launchTemplate = new ec2.LaunchTemplate(this, 'Wiki7LaunchTemplate', {
      instanceType: ec2.InstanceType.of(
        ec2.InstanceClass.T4G,
        ec2.InstanceSize.SMALL
      ),
      machineImage: ec2.MachineImage.latestAmazonLinux2023({
        cpuType: ec2.AmazonLinuxCpuType.ARM_64,
      }),
      userData,
      role: ec2Role,
      securityGroup: ec2SecurityGroup,
      blockDevices: [
        {
          deviceName: '/dev/xvda',
          volume: ec2.BlockDeviceVolume.ebs(30, {
            volumeType: ec2.EbsDeviceVolumeType.GP3,
            encrypted: true,
          }),
        },
      ],
      keyPair: props.keyPairName
        ? ec2.KeyPair.fromKeyPairName(this, 'KeyPair', props.keyPairName)
        : undefined,
      requireImdsv2: true,
    });

    // Auto Scaling Group (min:1, max:2 for cost control)
    this.autoScalingGroup = new autoscaling.AutoScalingGroup(
      this,
      'Wiki7ASG',
      {
        vpc,
        launchTemplate,
        minCapacity: 1,
        maxCapacity: 2,
        desiredCapacity: 1,
        vpcSubnets: { subnetType: ec2.SubnetType.PUBLIC },
        healthChecks: autoscaling.HealthChecks.ec2({
          gracePeriod: cdk.Duration.minutes(5),
        }),
        updatePolicy: autoscaling.UpdatePolicy.rollingUpdate({
          maxBatchSize: 1,
          minInstancesInService: 0,
        }),
      }
    );

    // CPU-based scaling policy
    this.autoScalingGroup.scaleOnCpuUtilization('CpuScaling', {
      targetUtilizationPercent: 70,
      cooldown: cdk.Duration.minutes(5),
    });

    // Create Lambda function to initialize S3 directories
    const s3DirectoriesLambdaRole = new iam.Role(
      this,
      'S3DirectoriesLambdaRole',
      {
        assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
        managedPolicies: [
          iam.ManagedPolicy.fromAwsManagedPolicyName(
            'service-role/AWSLambdaBasicExecutionRole'
          ),
        ],
      }
    );

    s3DirectoriesLambdaRole.addToPolicy(
      new iam.PolicyStatement({
        actions: ['s3:PutObject'],
        resources: [`${this.mediawikiStorageBucket.bucketArn}/*`],
      })
    );

    const s3DirectoriesFunction = new lambda.Function(
      this,
      'S3DirectoriesLambda',
      {
        runtime: lambda.Runtime.PYTHON_3_11,
        handler: 's3_directories.lambda_handler',
        code: lambda.Code.fromAsset(
          path.join(__dirname, '../lambda/s3-directories')
        ),
        timeout: cdk.Duration.seconds(30),
        role: s3DirectoriesLambdaRole,
      }
    );

    new cr.AwsCustomResource(this, 'CreateS3Directories', {
      onCreate: {
        service: 'Lambda',
        action: 'invoke',
        parameters: {
          FunctionName: s3DirectoriesFunction.functionName,
          Payload: JSON.stringify({
            RequestType: 'Create',
            ResourceProperties: {
              BucketName: this.mediawikiStorageBucket.bucketName,
              Directories: ['assets', 'images'],
            },
          }),
        },
        physicalResourceId: cr.PhysicalResourceId.of('S3DirectoriesResource'),
      },
      onUpdate: {
        service: 'Lambda',
        action: 'invoke',
        parameters: {
          FunctionName: s3DirectoriesFunction.functionName,
          Payload: JSON.stringify({
            RequestType: 'Update',
            ResourceProperties: {
              BucketName: this.mediawikiStorageBucket.bucketName,
              Directories: ['assets', 'images'],
            },
          }),
        },
        physicalResourceId: cr.PhysicalResourceId.of('S3DirectoriesResource'),
      },
      onDelete: {
        service: 'Lambda',
        action: 'invoke',
        parameters: {
          FunctionName: s3DirectoriesFunction.functionName,
          Payload: JSON.stringify({
            RequestType: 'Delete',
            ResourceProperties: {
              BucketName: this.mediawikiStorageBucket.bucketName,
              Directories: ['assets', 'images'],
            },
          }),
        },
        physicalResourceId: cr.PhysicalResourceId.of('S3DirectoriesResource'),
      },
      policy: cr.AwsCustomResourcePolicy.fromStatements([
        new iam.PolicyStatement({
          actions: ['lambda:InvokeFunction'],
          resources: [s3DirectoriesFunction.functionArn],
        }),
      ]),
    });

    // Tags for cost tracking
    cdk.Tags.of(this.autoScalingGroup).add('Project', 'Wiki7');
    cdk.Tags.of(this.autoScalingGroup).add('Component', 'Compute');
    cdk.Tags.of(this.mediawikiStorageBucket).add('Project', 'Wiki7');
    cdk.Tags.of(this.mediawikiStorageBucket).add('Component', 'Storage');

    // Outputs
    new cdk.CfnOutput(this, 'MediaWikiStorageBucketName', {
      value: this.mediawikiStorageBucket.bucketName,
      description: 'S3 bucket name for MediaWiki storage',
    });

    new cdk.CfnOutput(this, 'AutoScalingGroupName', {
      value: this.autoScalingGroup.autoScalingGroupName,
      description: 'Auto Scaling Group name',
    });
  }
}
