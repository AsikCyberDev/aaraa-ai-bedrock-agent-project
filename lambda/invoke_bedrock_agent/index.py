import json
import os
import boto3
import asyncio
from botocore.exceptions import ClientError

bedrock_runtime = boto3.client('bedrock-runtime')
dynamodb = boto3.resource('dynamodb')
agent_table = dynamodb.Table(os.environ['AGENT_TABLE_NAME'])
api_gateway_management = boto3.client('apigatewaymanagementapi', endpoint_url=os.environ['WEBSOCKET_API_ENDPOINT'])

async def handler(event, context):
    print(f"Received event: {json.dumps(event)}")

    connection_id = event['requestContext']['connectionId']
    body = json.loads(event['body'])
    chatbot_id = body['chatbotId']
    input_text = body['inputText']

    try:
        # Get agent details
        agent_details = get_agent_details(chatbot_id)

        # Invoke Bedrock Agent
        response = bedrock_runtime.invoke_agent(
            agentId=agent_details['agentId'],
            agentAliasId=agent_details['agentAliasId'],
            sessionId=connection_id,  # Using WebSocket connection ID as session ID
            inputText=input_text
        )

        # Process streaming response
        await process_streaming_response(response, connection_id)

        return {
            'statusCode': 200,
            'body': json.dumps('Agent invocation completed')
        }
    except Exception as e:
        print(f"Error invoking Bedrock Agent: {str(e)}")
        await send_error_to_client(connection_id, str(e))
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error invoking Bedrock Agent: {str(e)}")
        }

def get_agent_details(chatbot_id):
    try:
        response = agent_table.get_item(Key={'chatbotId': chatbot_id})
        return response['Item']
    except ClientError as e:
        print(f"Error fetching agent details: {e.response['Error']['Message']}")
        raise

async def process_streaming_response(response, connection_id):
    for event in response['completion']:
        chunk = event['chunk']
        chunk_data = json.loads(chunk['bytes'].decode())

        if 'delta' in chunk_data:
            # Send the text chunk to the WebSocket client
            await send_to_connection(connection_id, chunk_data['delta']['text'])
        elif 'error' in chunk_data:
            # Send error message to the WebSocket client
            await send_error_to_client(connection_id, chunk_data['error']['message'])

async def send_to_connection(connection_id, data):
    try:
        await api_gateway_management.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps({'type': 'response', 'content': data})
        )
    except ClientError as e:
        print(f"Error sending message to WebSocket: {e.response['Error']['Message']}")

async def send_error_to_client(connection_id, error_message):
    try:
        await api_gateway_management.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps({'type': 'error', 'content': error_message})
        )
    except ClientError as e:
        print(f"Error sending error message to WebSocket: {e.response['Error']['Message']}")