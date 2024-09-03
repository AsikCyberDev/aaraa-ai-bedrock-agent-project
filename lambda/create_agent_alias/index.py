import json
import boto3
from botocore.exceptions import ClientError

bedrock_agent = boto3.client('bedrock-agent')

def handler(event, context):
    print(f"Received event: {json.dumps(event)}")

    agent_id = event['agentId']
    chatbot = event['chatbot']

    try:
        # Create an agent alias
        agent_alias = create_agent_alias(agent_id, chatbot)

        return {
            'statusCode': 200,
            'body': json.dumps(agent_alias)
        }
    except Exception as e:
        print(f"Error creating Agent Alias: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error creating Agent Alias: {str(e)}")
        }

def create_agent_alias(agent_id, chatbot):
    alias_name = f"Alias-{chatbot['name']}"

    try:
        response = bedrock_agent.create_agent_alias(
            agentId=agent_id,
            agentAliasName=alias_name
        )

        agent_alias = response['agentAlias']
        print(f"Agent Alias created: {json.dumps(agent_alias)}")
        return agent_alias
    except ClientError as e:
        print(f"Error creating Agent Alias: {e.response['Error']['Message']}")
        raise