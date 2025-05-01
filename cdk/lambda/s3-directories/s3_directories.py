import boto3
import cfnresponse
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info(f"Received event: {event}")
    
    # Extract properties
    request_type = event['RequestType']
    properties = event.get('ResourceProperties', {})
    bucket_name = properties.get('BucketName')
    directories = properties.get('Directories', [])
    
    physical_id = f"s3-directories-{bucket_name}"
    
    # Initialize S3 client
    s3 = boto3.client('s3')
    
    try:
        if request_type in ['Create', 'Update']:
            logger.info(f"Creating directories in bucket {bucket_name}")
            
            for directory in directories:
                # Ensure the directory ends with a slash
                if not directory.endswith('/'):
                    directory = f"{directory}/"
                
                logger.info(f"Creating directory: {directory}")
                
                # Create an empty object to represent the directory
                s3.put_object(
                    Bucket=bucket_name,
                    Key=directory,
                    Body=''
                )
            
            cfnresponse.send(event, context, cfnresponse.SUCCESS, 
                             {"Message": f"Created directories: {', '.join(directories)}"},
                             physical_id)
        elif request_type == 'Delete':
            # We don't delete the directories when the stack is deleted
            logger.info("Delete request - not removing directories")
            cfnresponse.send(event, context, cfnresponse.SUCCESS, 
                             {"Message": "Directories preserved"}, 
                             physical_id)
        else:
            logger.error(f"Unexpected request type: {request_type}")
            cfnresponse.send(event, context, cfnresponse.FAILED, 
                             {"Error": f"Unexpected request type: {request_type}"}, 
                             physical_id)
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        cfnresponse.send(event, context, cfnresponse.FAILED, 
                         {"Error": str(e)}, 
                         physical_id)