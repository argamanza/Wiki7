import { Construct } from 'constructs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as elbv2 from 'aws-cdk-lib/aws-elasticloadbalancingv2';
import * as path from 'path';
import { Platform } from 'aws-cdk-lib/aws-ecr-assets';
import * as rds from 'aws-cdk-lib/aws-rds';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as cdk from 'aws-cdk-lib';

interface ApplicationStackProps {
  vpc: ec2.Vpc;
  dbInstance: rds.DatabaseInstance;
  dbSecret: secretsmanager.Secret;
  mediawikiSecurityGroup: ec2.SecurityGroup;
}

export class ApplicationStack extends Construct {
  readonly alb: elbv2.ApplicationLoadBalancer;

  constructor(scope: Construct, id: string, props: ApplicationStackProps) {
    super(scope, id);

    const { vpc, dbInstance, dbSecret, mediawikiSecurityGroup } = props;

    // Create ECS Cluster
    const cluster = new ecs.Cluster(this, 'Wiki7Cluster', {
      vpc,
      containerInsightsV2: ecs.ContainerInsights.ENABLED,
    });

    // IAM Role for ECS tasks
    const taskRole = new iam.Role(this, 'Wiki7TaskRole', {
      assumedBy: new iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
      description: 'IAM role for MediaWiki ECS containers',
    });

    taskRole.addManagedPolicy(
      iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AmazonECSTaskExecutionRolePolicy')
    );

    dbSecret.grantRead(taskRole);

    // Create S3 bucket for MediaWiki storage
    const mediawikiStorageBucket = new s3.Bucket(this, 'Wiki7StorageBucket', {
        bucketName: `wiki7-storage`,
        encryption: s3.BucketEncryption.S3_MANAGED,
        blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
        versioned: true,
        removalPolicy: cdk.RemovalPolicy.RETAIN,

        // Lifecycle rule to expire old versions after 7 days
        lifecycleRules: [
          {
            id: 'ExpireOldVersions',
            enabled: true,
            noncurrentVersionExpiration: cdk.Duration.days(7),  // Keep old versions for 7 days
            
            // Delete markers expiration
            expiredObjectDeleteMarker: true,
          }
        ],
    });
    
    // Grant ECS task role access to S3
    mediawikiStorageBucket.grantReadWrite(taskRole);

    // Log Group for container logs
    const logGroup = new logs.LogGroup(this, 'Wiki7LogGroup', {
      retention: logs.RetentionDays.ONE_MONTH,
    });

    // Task Definition
    const taskDefinition = new ecs.FargateTaskDefinition(this, 'Wiki7TaskDef', {
      cpu: 512,
      memoryLimitMiB: 1024,
      taskRole,
    });

    const container = taskDefinition.addContainer('MediaWikiContainer', {
      image: ecs.ContainerImage.fromAsset(path.join(__dirname, '../../docker'), {
        platform: Platform.LINUX_AMD64,
      }),
      logging: ecs.LogDriver.awsLogs({
        logGroup,
        streamPrefix: 'mediawiki',
      }),
      environment: {
        MEDIAWIKI_DB_HOST: dbInstance.dbInstanceEndpointAddress,
        MEDIAWIKI_DB_NAME: 'wikidb',
        MEDIAWIKI_DB_USER: 'wikiuser',
        WIKI_ENV: 'production'
      },
    });

    container.addSecret('MEDIAWIKI_DB_PASSWORD', ecs.Secret.fromSecretsManager(dbSecret, 'password'));

    container.addPortMappings({
      containerPort: 80,
      protocol: ecs.Protocol.TCP,
    });

    // Create Fargate Service
    const fargateService = new ecs.FargateService(this, 'Wiki7Service', {
      cluster,
      taskDefinition,
      desiredCount: 1,
      assignPublicIp: true,
      securityGroups: [mediawikiSecurityGroup],
      vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS },
    });

    // ALB Security Group
    const albSecurityGroup = new ec2.SecurityGroup(this, 'Wiki7AlbSecurityGroup', {
      vpc,
      description: 'Allow HTTP traffic to ALB from anywhere',
      allowAllOutbound: true,
    });

    albSecurityGroup.addIngressRule(ec2.Peer.anyIpv4(), ec2.Port.tcp(80), 'Allow HTTP traffic from anywhere');

    // Application Load Balancer
    this.alb = new elbv2.ApplicationLoadBalancer(this, 'Wiki7Alb', {
      vpc,
      internetFacing: true,
      securityGroup: albSecurityGroup,
      vpcSubnets: { subnetType: ec2.SubnetType.PUBLIC },
      loadBalancerName: 'Wiki7Alb',
    });

    // Listener and Target Group
    const listener = this.alb.addListener('Wiki7AlbListener', {
      port: 80,
      open: true,
    });

    listener.addTargets('Wiki7AlbTargets', {
      port: 80,
      targets: [fargateService],
      healthCheck: {
        path: '/',
        healthyHttpCodes: '200-399',
      },
    });
  }
}
