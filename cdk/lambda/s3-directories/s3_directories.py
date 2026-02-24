import boto3
import botocore.exceptions
import cfnresponse
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    request_id = event.get('RequestId', 'unknown')
    logger.info(f"[{request_id}] Received event: {event}")

    # Extract properties
    request_type = event.get('RequestType')
    if not request_type:
        logger.error(f"[{request_id}] Missing RequestType in event")
        cfnresponse.send(
            event, context, cfnresponse.FAILED,
            {"Error": "Missing RequestType in event"},
            f"s3-directories-error"
        )
        return

    properties = event.get('ResourceProperties', {})
    bucket_name = properties.get('BucketName')
    directories = properties.get('Directories', [])

    # Validate required parameters
    if not bucket_name:
        error_msg = "Missing required property: BucketName"
        logger.error(f"[{request_id}] {error_msg}")
        cfnresponse.send(
            event, context, cfnresponse.FAILED,
            {"Error": error_msg},
            f"s3-directories-error"
        )
        return

    if not directories or not isinstance(directories, list):
        error_msg = "Missing or invalid property: Directories (must be a non-empty list)"
        logger.error(f"[{request_id}] {error_msg}")
        cfnresponse.send(
            event, context, cfnresponse.FAILED,
            {"Error": error_msg},
            f"s3-directories-error"
        )
        return

    physical_id = f"s3-directories-{bucket_name}"

    # Initialize S3 client
    s3 = boto3.client('s3')

    try:
        if request_type in ['Create', 'Update']:
            logger.info(f"[{request_id}] Creating directories in bucket {bucket_name}")

            created = []
            for directory in directories:
                # Validate directory name (no path traversal, no special chars)
                if '..' in directory or '/' in directory.strip('/') or not directory.strip('/'):
                    logger.warning(f"[{request_id}] Skipping invalid directory name: {directory}")
                    continue

                # Ensure the directory ends with a slash
                if not directory.endswith('/'):
                    directory = f"{directory}/"

                logger.info(f"[{request_id}] Creating directory: {directory}")

                try:
                    s3.put_object(
                        Bucket=bucket_name,
                        Key=directory,
                        Body=''
                    )
                    created.append(directory)
                except botocore.exceptions.ClientError as e:
                    error_code = e.response['Error']['Code']
                    if error_code == 'NoSuchBucket':
                        raise ValueError(f"Bucket '{bucket_name}' does not exist") from e
                    elif error_code == 'AccessDenied':
                        raise PermissionError(
                            f"Access denied when writing to bucket '{bucket_name}'"
                        ) from e
                    else:
                        raise

            cfnresponse.send(
                event, context, cfnresponse.SUCCESS,
                {"Message": f"Created directories: {', '.join(created)}"},
                physical_id
            )

        elif request_type == 'Delete':
            # We don't delete the directories when the stack is deleted
            logger.info(f"[{request_id}] Delete request - not removing directories")
            cfnresponse.send(
                event, context, cfnresponse.SUCCESS,
                {"Message": "Directories preserved"},
                physical_id
            )

        else:
            error_msg = f"Unexpected request type: {request_type}"
            logger.error(f"[{request_id}] {error_msg}")
            cfnresponse.send(
                event, context, cfnresponse.FAILED,
                {"Error": error_msg},
                physical_id
            )

    except ValueError as e:
        logger.error(f"[{request_id}] Validation error: {str(e)}")
        cfnresponse.send(
            event, context, cfnresponse.FAILED,
            {"Error": f"Validation error: {str(e)}"},
            physical_id
        )
    except PermissionError as e:
        logger.error(f"[{request_id}] Permission error: {str(e)}")
        cfnresponse.send(
            event, context, cfnresponse.FAILED,
            {"Error": f"Permission error: {str(e)}"},
            physical_id
        )
    except botocore.exceptions.ClientError as e:
        error_code = e.response['Error']['Code']
        error_msg = e.response['Error']['Message']
        logger.error(f"[{request_id}] AWS ClientError ({error_code}): {error_msg}")
        cfnresponse.send(
            event, context, cfnresponse.FAILED,
            {"Error": f"AWS error ({error_code}): {error_msg}"},
            physical_id
        )
    except Exception as e:
        logger.error(f"[{request_id}] Unexpected error: {type(e).__name__}: {str(e)}")
        cfnresponse.send(
            event, context, cfnresponse.FAILED,
            {"Error": f"Unexpected error: {str(e)}"},
            physical_id
        )
