import json
import os
import boto3

stepfunctions = boto3.client('stepfunctions')

def handler(event, context):
    print(f"Received event: {json.dumps(event)}")

    # Extract chatbot details from the event
    detail = event['detail']
    chatbot_id = detail['chatbotId']  # Changed from 'id' to 'chatbotId'
    project_id = detail['projectId']

    if detail['type'] != 'BEDROCK_AGENT':
        print(f"Chatbot {chatbot_id} is not a Bedrock Agent. Skipping agent creation.")
        return

    try:
        # Start the Step Functions workflow
        response = stepfunctions.start_execution(
            stateMachineArn=os.environ['STATE_MACHINE_ARN'],
            input=json.dumps({
                'chatbotId': chatbot_id,
                'projectId': project_id,
                'name': detail['name'],
                'description': detail['description'],
                'language': detail['language'],
                'documents': detail['documents']
            })
        )
        print(f"Step Functions execution started: {response['executionArn']}")
        return {
            'statusCode': 200,
            'body': json.dumps(f"Bedrock Agent creation process started for chatbot {chatbot_id}")
        }
    except Exception as e:
        print(f"Error starting Step Functions execution: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error starting Bedrock Agent creation process: {str(e)}")
        }