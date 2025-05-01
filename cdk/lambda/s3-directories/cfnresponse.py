# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
import logging
import urllib.request

SUCCESS = "SUCCESS"
FAILED = "FAILED"

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def send(event, context, responseStatus, responseData, physicalResourceId=None, noEcho=False, reason=None):
    responseUrl = event['ResponseURL']

    logger.info(f"ResponseURL: {responseUrl}")

    responseBody = {
        'Status': responseStatus,
        'Reason': reason or f"See the details in CloudWatch Log Stream: {context.log_stream_name}",
        'PhysicalResourceId': physicalResourceId or context.log_stream_name,
        'StackId': event['StackId'],
        'RequestId': event['RequestId'],
        'LogicalResourceId': event['LogicalResourceId'],
        'NoEcho': noEcho,
        'Data': responseData
    }

    json_responseBody = json.dumps(responseBody)

    logger.info(f"Response body: {json_responseBody}")

    headers = {
        'content-type': '',
        'content-length': str(len(json_responseBody))
    }

    try:
        req = urllib.request.Request(url=responseUrl,
                                    data=json_responseBody.encode('utf-8'),
                                    headers=headers,
                                    method='PUT')
        with urllib.request.urlopen(req) as response:
            logger.info(f"Status code: {response.status}")
            logger.info(f"Status message: {response.reason}")
    except Exception as e:
        logger.error(f"Failed sending response: {str(e)}")
        raise e