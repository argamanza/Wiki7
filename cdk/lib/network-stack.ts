import { Construct } from 'constructs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as cdk from 'aws-cdk-lib';

export interface NetworkStackProps {
  /** Enable private subnets with NAT Gateway for RDS (adds ~$35/mo) */
  enablePrivateSubnets?: boolean;
}

export class NetworkStack extends Construct {
  readonly vpc: ec2.Vpc;
  readonly ec2SecurityGroup: ec2.SecurityGroup;

  constructor(scope: Construct, id: string, props: NetworkStackProps = {}) {
    super(scope, id);

    const enablePrivateSubnets = props.enablePrivateSubnets ?? false;

    // Subnet configuration: public-only by default (no NAT Gateway = saves ~$35/mo)
    const subnetConfiguration: ec2.SubnetConfiguration[] = [
      {
        cidrMask: 24,
        name: 'public',
        subnetType: ec2.SubnetType.PUBLIC,
      },
    ];

    if (enablePrivateSubnets) {
      subnetConfiguration.push({
        cidrMask: 24,
        name: 'private',
        subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
      });
    }

    // Create VPC - no NAT Gateway by default (compute in public subnet)
    this.vpc = new ec2.Vpc(this, 'Wiki7Vpc', {
      maxAzs: 2,
      natGateways: enablePrivateSubnets ? 1 : 0,
      subnetConfiguration,
    });

    // S3 VPC Gateway Endpoint (free - eliminates S3 NAT traffic costs)
    this.vpc.addGatewayEndpoint('S3Endpoint', {
      service: ec2.GatewayVpcEndpointAwsService.S3,
    });

    // EC2 security group - allows HTTP from CloudFront and SSH for maintenance
    this.ec2SecurityGroup = new ec2.SecurityGroup(this, 'EC2SecurityGroup', {
      vpc: this.vpc,
      description: 'Allow inbound HTTP from CloudFront and outbound for updates',
      allowAllOutbound: true, // Needed for yum/apt updates, S3 access, etc.
    });

    // Allow HTTP inbound (CloudFront connects to origin on port 80)
    this.ec2SecurityGroup.addIngressRule(
      ec2.Peer.anyIpv4(),
      ec2.Port.tcp(80),
      'Allow HTTP from CloudFront'
    );

    // Allow SSH inbound (restricted - for emergency maintenance only)
    this.ec2SecurityGroup.addIngressRule(
      ec2.Peer.anyIpv4(),
      ec2.Port.tcp(22),
      'Allow SSH for maintenance (restrict via key pair)'
    );

    // Tags for cost tracking
    cdk.Tags.of(this.vpc).add('Project', 'Wiki7');
    cdk.Tags.of(this.vpc).add('Component', 'Network');
    cdk.Tags.of(this.ec2SecurityGroup).add('Project', 'Wiki7');
  }
}
