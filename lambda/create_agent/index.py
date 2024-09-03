import json
import os
import boto3
import re
import uuid
from botocore.exceptions import ClientError

bedrock_agent = boto3.client('bedrock-agent')
dynamodb = boto3.resource('dynamodb')
chatbot_table = dynamodb.Table('InfrastructureStack-ChatbotTable881A2A75-13FEN4HTYJS09')

def handler(event, context):
    print(f"Received event: {json.dumps(event)}")
    chatbot_id = event['chatbotId']
    project_id = event['projectId']

    if not check_chatbot_exists(chatbot_id, project_id):
        return {
            'statusCode': 404,
            'body': json.dumps(f"Chatbot not found for id: {chatbot_id} and projectId: {project_id}")
        }

    try:
        chatbot = get_chatbot(chatbot_id, project_id)
        agent = create_bedrock_agent(chatbot)
        return {
            'statusCode': 200,
            'body': json.dumps(agent)
        }
    except Exception as e:
        print(f"Error creating Bedrock Agent: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error creating Bedrock Agent: {str(e)}")
        }

def get_chatbot(chatbot_id, project_id):
    try:
        response = chatbot_table.get_item(Key={'id': chatbot_id, 'projectId': project_id})
        if 'Item' not in response:
            raise ValueError(f"Chatbot not found for id: {chatbot_id} and projectId: {project_id}")
        return response['Item']
    except ClientError as e:
        print(f"Error fetching chatbot: {e.response['Error']['Message']}")
        raise
    except Exception as e:
        print(f"Unexpected error in get_chatbot: {str(e)}")
        raise

def sanitize_agent_name(name):
    # Remove any characters that are not alphanumeric, underscore, or hyphen
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '', name)

    # Ensure the name starts with an alphanumeric character
    if not sanitized[0].isalnum():
        sanitized = 'A' + sanitized

    # Truncate to 100 characters if longer
    sanitized = sanitized[:100]

    # Ensure the name is at least 1 character long
    if len(sanitized) == 0:
        sanitized = 'Agent'

    return sanitized

def create_bedrock_agent(chatbot):
    # Sanitize the agent name and append a unique identifier
    base_name = chatbot.get('name', 'Agent')
    unique_suffix = uuid.uuid4().hex[:8]  # Generate a short unique identifier
    agent_name = sanitize_agent_name(f"Agent-{base_name}-{unique_suffix}")

    # Ensure the instruction is at least 40 characters long
    instruction = chatbot.get('agentInstruction', 'You are a helpful AI assistant. Please provide accurate and relevant information to user queries.')
    if len(instruction) < 40:
        instruction += " Please assist users to the best of your ability."

    foundation_model = chatbot.get('foundationModel', 'anthropic.claude-v2')
    role_arn = os.environ['AGENT_ROLE_ARN']

    # Convert session timeout to integer, default to 1800 if not provided
    idle_session_ttl = int(chatbot.get('sessionTimeout', 1800))

    # Only include customerEncryptionKeyArn if it's provided and not None
    encryption_key_arn = os.environ.get('CUSTOMER_ENCRYPTION_KEY_ARN')

    try:
        create_agent_params = {
            'agentName': agent_name,
            'instruction': instruction,
            'foundationModel': foundation_model,
            'agentResourceRoleArn': role_arn,
            'description': chatbot.get('description', ''),
            'idleSessionTTLInSeconds': idle_session_ttl,
        }

        if encryption_key_arn:
            create_agent_params['customerEncryptionKeyArn'] = encryption_key_arn

        response = bedrock_agent.create_agent(**create_agent_params)

        agent = response['agent']
        print(f"Bedrock Agent created: {agent}")
        return {
            'agentId': agent['agentId'],
            'agentArn': agent['agentArn'],
            'agentName': agent['agentName'],
            'chatbotId': chatbot['id'],
            'projectId': chatbot['projectId']
        }
    except ClientError as e:
        print(f"Error creating Bedrock Agent: {e.response['Error']['Message']}")
        raise

def check_chatbot_exists(chatbot_id, project_id):
    print(f"Checking existence of chatbot with id: {chatbot_id} and projectId: {project_id}")
    try:
        response = chatbot_table.get_item(Key={'id': chatbot_id, 'projectId': project_id})
        exists = 'Item' in response
        print(f"Chatbot exists: {exists}")
        return exists
    except ClientError as e:
        print(f"Error checking chatbot existence: {e.response['Error']['Message']}")
        return False
