import json
import boto3
from botocore.exceptions import ClientError

opensearch_serverless = boto3.client('opensearchserverless')

def handler(event, context):
    print(f"Received event: {json.dumps(event)}")

    try:
        collection_name = event['opensearchCollection']['Payload']['collectionName']
        collection_arn = event['opensearchCollection']['Payload']['collectionArn']
        chatbot_id = event['opensearchCollection']['Payload']['chatbotId']
    except KeyError as e:
        print(f"Error accessing key in event: {e}")
        return {
            'error': f"Missing key in event: {e}",
            'message': 'Error accessing input data'
        }

    try:
        response = opensearch_serverless.batch_get_collection(names=[collection_name])
        status = response['collectionDetails'][0]['status']

        return {
            'collectionName': collection_name,
            'collectionArn': collection_arn,
            'status': status,
            'chatbotId': chatbot_id
        }
    except ClientError as e:
        print(f"Error checking collection status: {e.response['Error']['Message']}")
        return {
            'error': str(e),
            'message': 'Error checking collection status'
        }