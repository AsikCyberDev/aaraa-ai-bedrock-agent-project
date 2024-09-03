import json
import boto3
from botocore.exceptions import ClientError

bedrock_agent = boto3.client('bedrock-agent')

def handler(event, context):
    print(f"Received event: {json.dumps(event)}")

    agent_id = event['agentId']

    try:
        # Prepare the agent
        prepared_agent = prepare_agent(agent_id)

        return {
            'statusCode': 200,
            'body': json.dumps(prepared_agent)
        }
    except Exception as e:
        print(f"Error preparing Agent: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error preparing Agent: {str(e)}")
        }

def prepare_agent(agent_id):
    try:
        response = bedrock_agent.prepare_agent(agentId=agent_id)
        print(f"Agent prepared: {json.dumps(response)}")
        return response
    except ClientError as e:
        print(f"Error preparing Agent: {e.response['Error']['Message']}")
        raise