import json
import os
import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb')
chatbot_table = dynamodb.Table(os.environ['CHATBOT_TABLE_NAME'])
agent_table = dynamodb.Table(os.environ['AGENT_TABLE_NAME'])

def handler(event, context):
    print(f"Received event: {json.dumps(event)}")

    chatbot_id = event['chatbotId']
    project_id = event['projectId']
    agent_id = event['agentId']
    agent_arn = event['agentArn']
    agent_alias_id = event['agentAliasId']

    try:
        # Update chatbot with agent details
        update_chatbot(chatbot_id, project_id, agent_id, agent_arn, agent_alias_id)

        # Store agent details in a separate table
        store_agent_details(event)

        return {
            'statusCode': 200,
            'body': json.dumps("Chatbot and Agent details updated successfully")
        }
    except Exception as e:
        print(f"Error updating Chatbot and Agent details: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error updating Chatbot and Agent details: {str(e)}")
        }

def update_chatbot(chatbot_id, project_id, agent_id, agent_arn, agent_alias_id):
    try:
        chatbot_table.update_item(
            Key={'id': chatbot_id, 'projectId': project_id},
            UpdateExpression="set agentId = :a, agentArn = :b, agentAliasId = :c, status = :s",
            ExpressionAttributeValues={
                ':a': agent_id,
                ':b': agent_arn,
                ':c': agent_alias_id,
                ':s': 'ACTIVE'
            },
            ReturnValues="UPDATED_NEW"
        )
        print(f"Chatbot {chatbot_id} updated with Bedrock Agent details")
    except ClientError as e:
        print(f"Error updating Chatbot: {e.response['Error']['Message']}")
        raise

def store_agent_details(agent_info):
    try:
        agent_table.put_item(Item={
            'chatbotId': agent_info['chatbotId'],
            'projectId': agent_info['projectId'],
            'agentId': agent_info['agentId'],
            'agentArn': agent_info['agentArn'],
            'agentAliasId': agent_info['agentAliasId'],
            'knowledgeBaseId': agent_info.get('knowledgeBaseId'),
            'actionGroups': agent_info.get('actionGroups', []),
            'status': 'ACTIVE',
            'createdAt': agent_info['createdAt']
        })
        print(f"Agent details stored for chatbot {agent_info['chatbotId']}")
    except ClientError as e:
        print(f"Error storing Agent details: {e.response['Error']['Message']}")
        raise