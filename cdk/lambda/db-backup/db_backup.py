import boto3
import botocore.exceptions
import os
import logging
import time
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# How long to wait for SSM command to complete (seconds)
COMMAND_TIMEOUT = 120
POLL_INTERVAL = 10


def lambda_handler(event, context):
    request_id = getattr(context, 'aws_request_id', 'unknown') if context else 'unknown'
    logger.info(f"[{request_id}] Database backup Lambda invoked")

    # Validate environment variables
    bucket_name = os.environ.get('BACKUP_BUCKET', '')
    asg_name = os.environ.get('ASG_NAME', '')

    if not bucket_name:
        error_msg = "Missing required environment variable: BACKUP_BUCKET"
        logger.error(f"[{request_id}] {error_msg}")
        return {'statusCode': 400, 'body': error_msg}

    if not asg_name:
        error_msg = "Missing required environment variable: ASG_NAME"
        logger.error(f"[{request_id}] {error_msg}")
        return {'statusCode': 400, 'body': error_msg}

    # Find the first running instance in the ASG
    try:
        instance_id = get_asg_instance(asg_name, request_id)
    except Exception as e:
        error_msg = f"Failed to find running instance in ASG '{asg_name}': {str(e)}"
        logger.error(f"[{request_id}] {error_msg}")
        return {'statusCode': 500, 'body': error_msg}

    if not instance_id:
        error_msg = f"No running instances found in ASG '{asg_name}'"
        logger.error(f"[{request_id}] {error_msg}")
        return {'statusCode': 404, 'body': error_msg}

    logger.info(f"[{request_id}] Found instance {instance_id} in ASG {asg_name}")

    # Generate backup filename with timestamp
    timestamp = datetime.utcnow().strftime('%Y-%m-%d_%H-%M-%S')
    backup_key = f"backups/wikidb-{timestamp}.sql.gz"

    # Execute mysqldump via SSM Run Command
    backup_command = (
        f"mysqldump --single-transaction --routines --triggers "
        f"--databases wikidb | gzip | "
        f"aws s3 cp - s3://{bucket_name}/{backup_key}"
    )

    try:
        result = run_ssm_command(instance_id, backup_command, request_id)
    except Exception as e:
        error_msg = f"Failed to execute backup command: {str(e)}"
        logger.error(f"[{request_id}] {error_msg}")
        return {'statusCode': 500, 'body': error_msg}

    if result['status'] == 'Success':
        success_msg = f"Backup completed: s3://{bucket_name}/{backup_key}"
        logger.info(f"[{request_id}] {success_msg}")
        return {'statusCode': 200, 'body': success_msg}
    else:
        error_msg = f"Backup command failed with status '{result['status']}': {result.get('output', 'no output')}"
        logger.error(f"[{request_id}] {error_msg}")
        return {'statusCode': 500, 'body': error_msg}


def get_asg_instance(asg_name: str, request_id: str) -> str:
    """Find the first InService instance in the Auto Scaling Group."""
    autoscaling_client = boto3.client('autoscaling')

    response = autoscaling_client.describe_auto_scaling_groups(
        AutoScalingGroupNames=[asg_name]
    )

    groups = response.get('AutoScalingGroups', [])
    if not groups:
        raise ValueError(f"ASG '{asg_name}' not found")

    instances = groups[0].get('Instances', [])
    for instance in instances:
        if instance.get('LifecycleState') == 'InService' and instance.get('HealthStatus') == 'Healthy':
            return instance['InstanceId']

    return ''


def run_ssm_command(instance_id: str, command: str, request_id: str) -> dict:
    """Execute a command on an EC2 instance via SSM Run Command and wait for result."""
    ssm_client = boto3.client('ssm')

    logger.info(f"[{request_id}] Sending SSM command to {instance_id}")

    try:
        response = ssm_client.send_command(
            InstanceIds=[instance_id],
            DocumentName='AWS-RunShellScript',
            Parameters={'commands': [command]},
            TimeoutSeconds=COMMAND_TIMEOUT,
            Comment=f'Wiki7 database backup (request: {request_id})',
        )
    except botocore.exceptions.ClientError as e:
        error_code = e.response['Error']['Code']
        raise RuntimeError(f"SSM SendCommand failed ({error_code}): {str(e)}") from e

    command_id = response['Command']['CommandId']
    logger.info(f"[{request_id}] SSM command ID: {command_id}")

    # Poll for command completion
    elapsed = 0
    while elapsed < COMMAND_TIMEOUT:
        time.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL

        try:
            result = ssm_client.get_command_invocation(
                CommandId=command_id,
                InstanceId=instance_id,
            )
        except ssm_client.exceptions.InvocationDoesNotExist:
            logger.info(f"[{request_id}] Command not yet registered, waiting...")
            continue
        except botocore.exceptions.ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'InvocationDoesNotExist':
                continue
            raise

        status = result.get('Status', '')
        if status in ('Success', 'Failed', 'TimedOut', 'Cancelled'):
            return {
                'status': status,
                'output': result.get('StandardOutputContent', ''),
                'error': result.get('StandardErrorContent', ''),
            }

        logger.info(f"[{request_id}] Command status: {status}, elapsed: {elapsed}s")

    return {
        'status': 'TimedOut',
        'output': f'Command did not complete within {COMMAND_TIMEOUT}s',
    }
