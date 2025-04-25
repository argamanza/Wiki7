import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as path from 'path';
import { Platform } from 'aws-cdk-lib/aws-ecr-assets';

export class Wiki7CdkStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // VPC with isolated networking and NAT for private resources
    const vpc = new ec2.Vpc(this, 'Wiki7Vpc', {
      maxAzs: 2,
      natGateways: 1,
      subnetConfiguration: [
        {
          cidrMask: 24,
          name: 'public',
          subnetType: ec2.SubnetType.PUBLIC,
        },
        {
          cidrMask: 24,
          name: 'private',
          subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
        },
      ],
    });

    // ECS cluster within the VPC
    const cluster = new ecs.Cluster(this, 'Wiki7Cluster', {
      vpc,
      containerInsightsV2: ecs.ContainerInsights.ENABLED,
    });

    // IAM role used by ECS tasks (application-level permissions)
    const taskRole = new iam.Role(this, 'Wiki7TaskRole', {
      assumedBy: new iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
      description: 'IAM role for MediaWiki containers',
    });

    taskRole.addManagedPolicy(
      iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AmazonECSTaskExecutionRolePolicy')
    );

    // Log group for ECS containers
    const logGroup = new logs.LogGroup(this, 'Wiki7LogGroup', {
      retention: logs.RetentionDays.ONE_MONTH,
    });

    // Fargate Task Definition for MediaWiki container
    const taskDefinition = new ecs.FargateTaskDefinition(this, 'Wiki7TaskDef', {
      cpu: 512,
      memoryLimitMiB: 1024,
      taskRole,
    });
    
    taskDefinition.addContainer('MediaWikiContainer', {
      image: ecs.ContainerImage.fromAsset(path.join(__dirname, '../../docker'), {
        platform: Platform.LINUX_AMD64,
      }),
      logging: ecs.LogDriver.awsLogs({
        logGroup,
        streamPrefix: 'mediawiki',
      }),
      environment: {
        MEDIAWIKI_DB_HOST: 'db-host-placeholder',
        MEDIAWIKI_DB_NAME: 'wikidb',
        MEDIAWIKI_DB_USER: 'wikiuser',
        MEDIAWIKI_DB_PASSWORD: 'secret',
      },
    });

    // Create security group for the MediaWiki Fargate service
    const mediawikiSG = new ec2.SecurityGroup(this, 'MediaWikiServiceSG', {
      vpc,
      description: 'Allow inbound traffic from ALB to MediaWiki',
      allowAllOutbound: true,
    });

    // Create the Fargate service
    const fargateService = new ecs.FargateService(this, 'MediaWikiService', {
      cluster,
      taskDefinition,
      assignPublicIp: true, // so it can receive traffic directly via ALB
      desiredCount: 1,
      securityGroups: [mediawikiSG],
      vpcSubnets: {
        subnetType: ec2.SubnetType.PUBLIC, // will be behind an ALB anyway
      },
    });
  }
}
