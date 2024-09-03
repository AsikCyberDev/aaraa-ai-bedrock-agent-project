import json
import os
import boto3
from botocore.exceptions import ClientError

bedrock_agent = boto3.client('bedrock-agent')
lambda_client = boto3.client('lambda')

def handler(event, context):
    print(f"Received event: {json.dumps(event)}")

    try:
        agent_id = json.loads(event['createAgent']['Payload']['body'])['agentId']
        agent_version = get_agent_version(agent_id)
        chatbot_id = event['chatbotId']

        action_groups = create_action_groups(agent_id, agent_version, chatbot_id)
        return {
            'statusCode': 200,
            'body': json.dumps(action_groups)
        }
    except KeyError as e:
        print(f"Error accessing key in event: {e}")
        return {
            'statusCode': 400,
            'body': json.dumps(f"Missing key in event: {e}")
        }
    except Exception as e:
        print(f"Error creating Action Groups: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error creating Action Groups: {str(e)}")
        }

def get_agent_version(agent_id):
    try:
        response = bedrock_agent.list_agent_versions(
            agentId=agent_id,
            maxResults=1
        )
        if response['agentVersionSummaries']:
            return response['agentVersionSummaries'][0]['agentVersion']
        else:
            raise Exception(f"No versions found for agent {agent_id}")
    except ClientError as e:
        print(f"Error fetching agent version: {e.response['Error']['Message']}")
        raise

def get_lambda_arn():
    try:
        # List Lambda functions and get the first one's ARN
        response = lambda_client.list_functions(MaxItems=1)
        if response['Functions']:
            return response['Functions'][0]['FunctionArn']
        else:
            raise Exception("No Lambda functions found in the account")
    except ClientError as e:
        print(f"Error listing Lambda functions: {e.response['Error']['Message']}")
        raise

def create_action_groups(agent_id, agent_version, chatbot_id):
    try:
        # Get a valid Lambda ARN from your account
        lambda_arn = get_lambda_arn()
        print(f"Using Lambda ARN: {lambda_arn}")

        action_groups_data = [
            {
                'name': 'ActionGroup1',
                'description': 'Description for Action Group 1',
                'lambdaArn': lambda_arn,
                'apiSchema': {
                    "openapi": "3.0.0",
                    "info": {"title": "ActionGroup1 API", "version": "1.0.0"},
                    "paths": {
                        "/example": {
                            "get": {
                                "summary": "Example endpoint",
                                "responses": {
                                    "200": {
                                        "description": "Successful response",
                                        "content": {
                                            "application/json": {
                                                "schema": {
                                                    "type": "object",
                                                    "properties": {
                                                        "message": {"type": "string"}
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        ]

        created_action_groups = []
        for action_group in action_groups_data:
            try:
                response = bedrock_agent.create_agent_action_group(
                    agentId=agent_id,
                    agentVersion=agent_version,
                    actionGroupName=action_group['name'],
                    description=action_group.get('description', ''),
                    actionGroupExecutor={
                        'lambda': action_group['lambdaArn']
                    },
                    apiSchema={
                        'httpMethod': 'GET',
                        'payload': json.dumps(action_group['apiSchema'])
                    }
                )
                created_action_group = response['agentActionGroup']
                print(f"Action Group created: {json.dumps(created_action_group)}")
                created_action_groups.append(created_action_group)
            except ClientError as e:
                print(f"Error creating Action Group: {e.response['Error']['Message']}")
                print(f"Full error response: {json.dumps(e.response)}")
                raise Exception(f"Failed to create Action Group: {e.response['Error']['Message']}")
        return created_action_groups
    except Exception as e:
        print(f"Error in create_action_groups: {str(e)}")
        raise