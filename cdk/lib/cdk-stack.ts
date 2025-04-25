import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as path from 'path';
import { Platform } from 'aws-cdk-lib/aws-ecr-assets';
import * as elbv2 from 'aws-cdk-lib/aws-elasticloadbalancingv2';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import * as rds from 'aws-cdk-lib/aws-rds';

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
    
    const container = taskDefinition.addContainer('MediaWikiContainer', {
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
    
    // Add port mapping
    container.addPortMappings({
      containerPort: 80,
      protocol: ecs.Protocol.TCP,
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

    const albSecurityGroup = new ec2.SecurityGroup(this, 'Wiki7ALBSecurityGroup', {
      vpc,
      description: 'Allow inbound HTTP from anywhere to ALB',
      allowAllOutbound: true,
    });
    
    albSecurityGroup.addIngressRule(ec2.Peer.anyIpv4(), ec2.Port.tcp(80), 'Allow HTTP traffic from anywhere');

    // Application Load Balancer
    const alb = new elbv2.ApplicationLoadBalancer(this, 'Wiki7ALB', {
      vpc,
      internetFacing: true,
      securityGroup: albSecurityGroup,
      vpcSubnets: { subnetType: ec2.SubnetType.PUBLIC },
      loadBalancerName: 'Wiki7ALB',
    });

    // Listener for port 80
    const listener = alb.addListener('Listener', {
      port: 80,
      open: true,
    });

    // Attach ECS service to ALB
    listener.addTargets('Wiki7EcsTargets', {
      port: 80,
      targets: [fargateService],
      healthCheck: {
        path: '/',
        healthyHttpCodes: '200-399',
      },
    });

    // Create a secret for the RDS database credentials
    const dbSecret = new secretsmanager.Secret(this, 'Wiki7DBSecret', {
      generateSecretString: {
        secretStringTemplate: JSON.stringify({ username: 'wikiuser' }),
        generateStringKey: 'password',
        excludePunctuation: true,
        includeSpace: false,
      },
      description: 'Database credentials for Wiki7 MediaWiki database',
    });

    // Security group for RDS (controls who can connect)
    const dbSecurityGroup = new ec2.SecurityGroup(this, 'Wiki7DBSecurityGroup', {
      vpc,
      description: 'Allow access to MariaDB from MediaWiki ECS service',
      allowAllOutbound: true,
    });

    // Allow only the Fargate Service security group to connect to the DB on port 3306
    dbSecurityGroup.addIngressRule(
      mediawikiSG,
      ec2.Port.tcp(3306),
      'Allow MediaWiki ECS Service to access database'
    );

    // Create the RDS database instance
    const dbInstance = new rds.DatabaseInstance(this, 'Wiki7Database', {
      engine: rds.DatabaseInstanceEngine.mariaDb({ version: rds.MariaDbEngineVersion.VER_10_5 }),
      vpc,
      vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS }, // Only private subnets
      securityGroups: [dbSecurityGroup],
      credentials: rds.Credentials.fromSecret(dbSecret),
      multiAz: false, // Single AZ for cost (can be changed later)
      allocatedStorage: 20, // GB
      maxAllocatedStorage: 100, // Allow it to grow if needed
      instanceType: ec2.InstanceType.of(
        ec2.InstanceClass.BURSTABLE3,
        ec2.InstanceSize.MICRO
      ), // Cheap, good for dev
      publiclyAccessible: false, // No direct public access
      removalPolicy: cdk.RemovalPolicy.DESTROY, // Auto-delete in dev (be careful in prod!)
      deletionProtection: false,
      backupRetention: cdk.Duration.days(7), // 7 days backup
      databaseName: 'wikidb',
    });
  
  }
}
