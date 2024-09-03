import boto3
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

lambda_client = boto3.client('lambda')

def handler(event, context):
    logger.info(f"Received event: {event}")
    try:
        lambda_functions = os.environ['LAMBDA_FUNCTIONS'].split(',')
        state_machine_arn = os.environ['STATE_MACHINE_ARN']
        websocket_url = os.environ['WEBSOCKET_URL']

        for function_name in lambda_functions:
            logger.info(f"Updating function: {function_name}")
            response = lambda_client.update_function_configuration(
                FunctionName=function_name,
                Environment={
                    'Variables': {
                        'STATE_MACHINE_ARN': state_machine_arn,
                        'WEBSOCKET_API_ENDPOINT': websocket_url
                    }
                }
            )
            logger.info(f"Update response: {response}")

        return {
            'statusCode': 200,
            'body': 'Lambda functions updated successfully'
        }
    except Exception as e:
        logger.error(f"Error updating Lambda functions: {str(e)}")
        raise