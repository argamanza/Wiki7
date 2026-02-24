import boto3
import botocore.exceptions
import os
import re
import logging
import time

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Valid AWS region pattern
REGION_PATTERN = re.compile(r'^[a-z]{2}(-[a-z]+-\d+)$')

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2


def validate_region(region: str) -> bool:
    """Validate that a string looks like a valid AWS region."""
    return bool(REGION_PATTERN.match(region))


def get_parameter_with_retry(ssm_client, parameter_name: str, region: str) -> str:
    """Get SSM parameter value with retry logic."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = ssm_client.get_parameter(
                Name=parameter_name,
                WithDecryption=True
            )
            return response['Parameter']['Value']
        except ssm_client.exceptions.ParameterNotFound:
            # No point retrying if parameter doesn't exist
            raise
        except botocore.exceptions.ClientError as e:
            error_code = e.response['Error']['Code']
            if attempt < MAX_RETRIES and error_code in ('ThrottlingException', 'InternalError'):
                logger.warning(
                    f"Attempt {attempt}/{MAX_RETRIES} failed with {error_code}, "
                    f"retrying in {RETRY_DELAY_SECONDS}s..."
                )
                time.sleep(RETRY_DELAY_SECONDS * attempt)
            else:
                raise


def put_parameter_with_retry(ssm_client, parameter_name: str, value: str, region: str) -> None:
    """Put SSM parameter value with retry logic."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            ssm_client.put_parameter(
                Name=parameter_name,
                Value=value,
                Type='String',
                Overwrite=True
            )
            return
        except botocore.exceptions.ClientError as e:
            error_code = e.response['Error']['Code']
            if attempt < MAX_RETRIES and error_code in ('ThrottlingException', 'InternalError'):
                logger.warning(
                    f"Attempt {attempt}/{MAX_RETRIES} failed with {error_code}, "
                    f"retrying in {RETRY_DELAY_SECONDS}s..."
                )
                time.sleep(RETRY_DELAY_SECONDS * attempt)
            else:
                raise


def lambda_handler(event, context):
    request_id = getattr(context, 'aws_request_id', 'unknown') if context else 'unknown'
    logger.info(f"[{request_id}] SSM sync invoked")

    # Read and validate environment variables
    source_region = os.environ.get('AWS_REGION', '')
    target_region = os.environ.get('TARGET_REGION', '')
    parameter_name = os.environ.get('PARAMETER_NAME', '')

    # Validate source region
    if not source_region or not validate_region(source_region):
        error_msg = f"Invalid or missing source region (AWS_REGION): '{source_region}'"
        logger.error(f"[{request_id}] {error_msg}")
        return {'statusCode': 400, 'body': error_msg}

    # Validate target region
    if not target_region or not validate_region(target_region):
        error_msg = f"Invalid or missing target region (TARGET_REGION): '{target_region}'"
        logger.error(f"[{request_id}] {error_msg}")
        return {'statusCode': 400, 'body': error_msg}

    # Validate parameter name
    if not parameter_name or not parameter_name.startswith('/'):
        error_msg = f"Invalid or missing parameter name: '{parameter_name}'"
        logger.error(f"[{request_id}] {error_msg}")
        return {'statusCode': 400, 'body': error_msg}

    # Prevent syncing to the same region
    if source_region == target_region:
        error_msg = f"Source and target regions are the same: '{source_region}'"
        logger.error(f"[{request_id}] {error_msg}")
        return {'statusCode': 400, 'body': error_msg}

    logger.info(
        f"[{request_id}] Syncing parameter '{parameter_name}' "
        f"from {source_region} to {target_region}"
    )

    ssm_source = boto3.client('ssm', region_name=source_region)
    ssm_target = boto3.client('ssm', region_name=target_region)

    # Read parameter from source region (with retry)
    try:
        value = get_parameter_with_retry(ssm_source, parameter_name, source_region)
    except ssm_source.exceptions.ParameterNotFound:
        error_msg = f"Parameter '{parameter_name}' not found in {source_region}"
        logger.error(f"[{request_id}] {error_msg}")
        return {'statusCode': 404, 'body': error_msg}
    except botocore.exceptions.ClientError as e:
        error_code = e.response['Error']['Code']
        error_msg = f"Failed to read parameter from {source_region}: {error_code}"
        logger.error(f"[{request_id}] {error_msg}: {str(e)}")
        return {'statusCode': 500, 'body': error_msg}

    # Write parameter to target region (with retry)
    try:
        put_parameter_with_retry(ssm_target, parameter_name, value, target_region)
    except botocore.exceptions.ClientError as e:
        error_code = e.response['Error']['Code']
        error_msg = f"Failed to write parameter to {target_region}: {error_code}"
        logger.error(f"[{request_id}] {error_msg}: {str(e)}")
        return {'statusCode': 500, 'body': error_msg}

    success_msg = f"Parameter '{parameter_name}' synced from {source_region} to {target_region}"
    logger.info(f"[{request_id}] {success_msg}")
    return {'statusCode': 200, 'body': success_msg}
