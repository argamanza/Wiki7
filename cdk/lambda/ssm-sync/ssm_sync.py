import boto3
import os

def lambda_handler(event, context):
    source_region = os.environ['AWS_REGION']
    target_region = os.environ['TARGET_REGION']
    parameter_name = os.environ['PARAMETER_NAME']

    ssm_source = boto3.client('ssm', region_name=source_region)
    ssm_target = boto3.client('ssm', region_name=target_region)

    # Read parameter
    try:
        response = ssm_source.get_parameter(
            Name=parameter_name,
            WithDecryption=False
        )
    except ssm_source.exceptions.ParameterNotFound:
        return {
            'statusCode': 404,
            'body': f'Parameter {parameter_name} not found in {source_region}'
        }

    value = response['Parameter']['Value']

    # Write parameter
    ssm_target.put_parameter(
        Name=parameter_name,
        Value=value,
        Type='String',
        Overwrite=True
    )

    return {
        'statusCode': 200,
        'body': f'Parameter {parameter_name} copied from {source_region} to {target_region}.'
    }
