import { Construct } from 'constructs';
import * as cdk from 'aws-cdk-lib';
import * as sns from 'aws-cdk-lib/aws-sns';
import * as snsSubscriptions from 'aws-cdk-lib/aws-sns-subscriptions';
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';
import * as cloudwatchActions from 'aws-cdk-lib/aws-cloudwatch-actions';
import * as autoscaling from 'aws-cdk-lib/aws-autoscaling';
import * as cloudfront from 'aws-cdk-lib/aws-cloudfront';
import * as budgets from 'aws-cdk-lib/aws-budgets';
import * as ce from 'aws-cdk-lib/aws-ce';

export interface MonitoringStackProps {
  /** Email address for alert notifications */
  alertEmail: string;
  /** Auto Scaling Group to monitor */
  autoScalingGroup: autoscaling.AutoScalingGroup;
  /** CloudFront distribution to monitor */
  distribution: cloudfront.Distribution;
  /** Monthly budget threshold in USD (default: $25) */
  budgetThresholdUsd?: number;
}

/**
 * Monitoring stack proportional to personal project scale.
 *
 * Includes:
 * - SNS topic for email alerts
 * - CloudWatch alarms for EC2 CPU and CloudFront errors
 * - AWS Budget alarm with configurable threshold
 */
export class MonitoringStack extends Construct {
  readonly alertTopic: sns.Topic;

  constructor(scope: Construct, id: string, props: MonitoringStackProps) {
    super(scope, id);

    const { alertEmail, autoScalingGroup, distribution } = props;
    const budgetThreshold = props.budgetThresholdUsd ?? 25;

    // SNS topic for all alerts
    this.alertTopic = new sns.Topic(this, 'Wiki7AlertTopic', {
      topicName: 'wiki7-alerts',
      displayName: 'Wiki7 Alerts',
    });

    this.alertTopic.addSubscription(
      new snsSubscriptions.EmailSubscription(alertEmail)
    );

    // EC2 CPU utilization alarm (>80% for 5 minutes)
    const cpuAlarm = new cloudwatch.Alarm(this, 'EC2CpuAlarm', {
      alarmName: 'wiki7-ec2-cpu-high',
      alarmDescription:
        'EC2 CPU utilization exceeds 80% for 5 minutes',
      metric: new cloudwatch.Metric({
        namespace: 'AWS/EC2',
        metricName: 'CPUUtilization',
        dimensionsMap: {
          AutoScalingGroupName: autoScalingGroup.autoScalingGroupName,
        },
        statistic: 'Average',
        period: cdk.Duration.minutes(5),
      }),
      threshold: 80,
      evaluationPeriods: 1,
      comparisonOperator:
        cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
      treatMissingData: cloudwatch.TreatMissingData.BREACHING,
    });
    cpuAlarm.addAlarmAction(new cloudwatchActions.SnsAction(this.alertTopic));

    // EC2 disk usage alarm (>85%) - uses CloudWatch Agent custom metric
    const diskAlarm = new cloudwatch.Alarm(this, 'EC2DiskAlarm', {
      alarmName: 'wiki7-ec2-disk-high',
      alarmDescription:
        'EC2 disk usage exceeds 85% (requires CloudWatch Agent)',
      metric: new cloudwatch.Metric({
        namespace: 'CWAgent',
        metricName: 'disk_used_percent',
        dimensionsMap: {
          AutoScalingGroupName: autoScalingGroup.autoScalingGroupName,
          path: '/',
          fstype: 'xfs',
        },
        statistic: 'Maximum',
        period: cdk.Duration.minutes(5),
      }),
      threshold: 85,
      evaluationPeriods: 1,
      comparisonOperator:
        cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    });
    diskAlarm.addAlarmAction(new cloudwatchActions.SnsAction(this.alertTopic));

    // CloudFront error rate alarm (>5% for 15 minutes)
    const cfErrorAlarm = new cloudwatch.Alarm(this, 'CloudFrontErrorAlarm', {
      alarmName: 'wiki7-cloudfront-error-rate',
      alarmDescription:
        'CloudFront 5xx error rate exceeds 5% for 15 minutes',
      metric: new cloudwatch.Metric({
        namespace: 'AWS/CloudFront',
        metricName: '5xxErrorRate',
        dimensionsMap: {
          DistributionId: distribution.distributionId,
          Region: 'Global',
        },
        statistic: 'Average',
        period: cdk.Duration.minutes(5),
      }),
      threshold: 5,
      evaluationPeriods: 3,
      comparisonOperator:
        cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    });
    cfErrorAlarm.addAlarmAction(
      new cloudwatchActions.SnsAction(this.alertTopic)
    );

    // AWS Budget alarm ($25/mo threshold with SNS notification)
    new budgets.CfnBudget(this, 'Wiki7MonthlyBudget', {
      budget: {
        budgetName: 'wiki7-monthly-budget',
        budgetType: 'COST',
        timeUnit: 'MONTHLY',
        budgetLimit: {
          amount: budgetThreshold,
          unit: 'USD',
        },
      },
      notificationsWithSubscribers: [
        {
          notification: {
            notificationType: 'ACTUAL',
            comparisonOperator: 'GREATER_THAN',
            threshold: 80,
            thresholdType: 'PERCENTAGE',
          },
          subscribers: [
            {
              subscriptionType: 'EMAIL',
              address: alertEmail,
            },
          ],
        },
        {
          notification: {
            notificationType: 'ACTUAL',
            comparisonOperator: 'GREATER_THAN',
            threshold: 100,
            thresholdType: 'PERCENTAGE',
          },
          subscribers: [
            {
              subscriptionType: 'EMAIL',
              address: alertEmail,
            },
          ],
        },
        {
          notification: {
            notificationType: 'FORECASTED',
            comparisonOperator: 'GREATER_THAN',
            threshold: 100,
            thresholdType: 'PERCENTAGE',
          },
          subscribers: [
            {
              subscriptionType: 'EMAIL',
              address: alertEmail,
            },
          ],
        },
      ],
    });

    // AWS Cost Anomaly Detection (free service)
    // Monitors for unexpected cost spikes using machine learning
    const anomalyMonitor = new ce.CfnAnomalyMonitor(this, 'Wiki7CostAnomalyMonitor', {
      monitorName: 'wiki7-cost-anomaly-monitor',
      monitorType: 'DIMENSIONAL',
      monitorDimension: 'SERVICE',
    });

    new ce.CfnAnomalySubscription(this, 'Wiki7CostAnomalySubscription', {
      subscriptionName: 'wiki7-cost-anomaly-alerts',
      monitorArnList: [anomalyMonitor.attrMonitorArn],
      subscribers: [
        {
          type: 'EMAIL',
          address: alertEmail,
        },
      ],
      frequency: 'DAILY',
      thresholdExpression: JSON.stringify({
        Dimensions: {
          Key: 'ANOMALY_TOTAL_IMPACT_ABSOLUTE',
          Values: ['5'],
          MatchOptions: ['GREATER_THAN_OR_EQUAL'],
        },
      }),
    });

    // Tags
    cdk.Tags.of(this).add('Project', 'Wiki7');
    cdk.Tags.of(this).add('Component', 'Monitoring');
  }
}
