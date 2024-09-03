import json
import os
import boto3
from botocore.exceptions import ClientError

bedrock_agent = boto3.client('bedrock-agent')
opensearch_serverless = boto3.client('opensearchserverless')

def handler(event, context):
    print(f"Received event: {json.dumps(event)}")

    try:
        chatbot_id = event['chatbotId']
        collection_arn = event['opensearchCollection']['Payload']['collectionArn']

        # Verify the OpenSearch collection
        verify_opensearch_collection(collection_arn)

        knowledge_base_name = f"KB-{chatbot_id[:20]}"  # Limit the name to 23 characters
        description = 'Knowledge base for the chatbot'
        role_arn = os.environ['KNOWLEDGE_BASE_ROLE_ARN']
        embedding_model_arn = os.environ['EMBEDDING_MODEL_ARN']

        response = bedrock_agent.create_knowledge_base(
            name=knowledge_base_name,
            description=description,
            roleArn=role_arn,
            knowledgeBaseConfiguration={
                'type': 'VECTOR',
                'vectorKnowledgeBaseConfiguration': {
                    'embeddingModelArn': embedding_model_arn
                }
            },
            storageConfiguration={
                'type': 'OPENSEARCH_SERVERLESS',
                'opensearchServerlessConfiguration': {
                    'collectionArn': collection_arn,
                    'vectorIndexName': 'bedrock-kb-index',
                    'fieldMapping': {
                        'vectorField': 'bedrock_embedding',
                        'textField': 'bedrock_text',
                        'metadataField': 'bedrock_metadata'
                    }
                }
            }
        )

        knowledge_base = response['knowledgeBase']
        print(f"Knowledge Base created: {json.dumps(knowledge_base)}")
        return {
            'statusCode': 200,
            'body': json.dumps({
                'knowledgeBase': knowledge_base,
                'chatbotId': chatbot_id
            })
        }
    except KeyError as e:
        print(f"Error accessing key in event: {e}")
        return {
            'statusCode': 400,
            'body': json.dumps(f"Missing key in event: {e}")
        }
    except ClientError as e:
        error_message = e.response['Error']['Message']
        print(f"Error creating Knowledge Base: {error_message}")
        print(f"Full error response: {json.dumps(e.response)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error creating Knowledge Base: {error_message}")
        }
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Unexpected error: {str(e)}")
        }

def verify_opensearch_collection(collection_arn):
    try:
        collection_name = collection_arn.split('/')[-1]
        print(f"Verifying OpenSearch collection: {collection_name}")

        response = opensearch_serverless.batch_get_collection(names=[collection_name])
        print(f"OpenSearch batch_get_collection response: {json.dumps(response)}")

        if not response.get('collectionDetails'):
            raise Exception(f"No collection details found for collection: {collection_name}")

        collection = response['collectionDetails'][0]
        print(f"OpenSearch collection details: {json.dumps(collection)}")

        if collection['status'] != 'ACTIVE':
            raise Exception(f"OpenSearch collection is not active. Current status: {collection['status']}")

        print(f"OpenSearch collection {collection_name} is verified and active.")
    except ClientError as e:
        error_message = e.response['Error']['Message']
        print(f"ClientError in verify_opensearch_collection: {error_message}")
        print(f"Full error response: {json.dumps(e.response)}")
        raise Exception(f"Error verifying OpenSearch collection: {error_message}")
    except Exception as e:
        print(f"Error verifying OpenSearch collection: {str(e)}")
        raise