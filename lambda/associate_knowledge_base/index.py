import json
import boto3
from botocore.exceptions import ClientError

bedrock_agent = boto3.client('bedrock-agent')

def handler(event, context):
    print(f"Received event: {json.dumps(event)}")

    try:
        agent_id = json.loads(event['createAgent']['Payload']['body'])['agentId']
        knowledge_base_id = event['knowledgeBase']['body']['knowledgeBase']['knowledgeBaseId']

        response = associate_knowledge_base(agent_id, knowledge_base_id)
        return {
            'statusCode': 200,
            'body': json.dumps(response)
        }
    except KeyError as e:
        print(f"Error accessing key in event: {e}")
        return {
            'statusCode': 400,
            'body': json.dumps(f"Missing key in event: {e}")
        }
    except Exception as e:
        print(f"Error associating Knowledge Base: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error associating Knowledge Base: {str(e)}")
        }

def associate_knowledge_base(agent_id, knowledge_base_id):
    try:
        response = bedrock_agent.associate_agent_knowledge_base(
            agentId=agent_id,
            knowledgeBaseId=knowledge_base_id,
            description='Associated knowledge base for the agent'
        )
        print(f"Knowledge Base {knowledge_base_id} associated with Agent {agent_id}")
        return response
    except ClientError as e:
        print(f"Error associating Knowledge Base: {e.response['Error']['Message']}")
        raise