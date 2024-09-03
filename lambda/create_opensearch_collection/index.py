import json
import os
import boto3
from botocore.exceptions import ClientError
import hashlib
import uuid
import time

opensearch_serverless = boto3.client('opensearchserverless')
ec2 = boto3.client('ec2')

def handler(event, context):
    print(f"Received event: {json.dumps(event)}")
    chatbot_id = event['chatbotId']
    collection_name = create_unique_name(chatbot_id)

    try:
        # Create security policy
        create_security_policy(collection_name)

        # Create or get network policy
        vpc_endpoint_id = create_or_get_network_policy(collection_name)

        # Create data access policy
        create_data_access_policy(collection_name)

        # Create collection
        collection_arn = create_collection(collection_name)

        # Wait for collection to be active
        wait_for_collection_active(collection_name)

        # Create index
        create_index(collection_name)

        return {
            'collectionName': collection_name,
            'collectionArn': collection_arn,
            'status': 'ACTIVE',
            'chatbotId': chatbot_id,
            'vpcEndpointId': vpc_endpoint_id
        }
    except Exception as e:
        print(f"Error creating OpenSearch Serverless collection: {str(e)}")
        raise

def create_unique_name(chatbot_id):
    short_hash = hashlib.md5(chatbot_id.encode()).hexdigest()[:4]
    unique_id = str(uuid.uuid4())[:4]
    return f"kb-{short_hash}-{unique_id}"

def create_security_policy(collection_name):
    policy_name = f"{collection_name}-security-policy"
    try:
        opensearch_serverless.create_security_policy(
            name=policy_name,
            policy=json.dumps({
                "Rules": [{"ResourceType": "collection", "Resource": [f"collection/{collection_name}"]}],
                "AWSOwnedKey": True
            }),
            type="encryption"
        )
        print(f"Security policy created: {policy_name}")
    except ClientError as e:
        print(f"Error creating security policy: {e.response['Error']['Message']}")
        raise

def create_or_get_network_policy(collection_name):
    policy_name = f"{collection_name}-network-policy"
    vpc_id = os.environ['VPC_ID']
    subnet_ids = os.environ['SUBNET_IDS'].split(',')
    security_group_id = os.environ['SECURITY_GROUP_ID']

    try:
        # Try to create a new VPC endpoint
        response = opensearch_serverless.create_vpc_endpoint(
            name=policy_name,
            vpcId=vpc_id,
            subnetIds=subnet_ids,
            securityGroupIds=[security_group_id]
        )
        vpc_endpoint_id = response['vpcEndpoint']['id']
        print(f"New VPC endpoint created: {vpc_endpoint_id}")
        return vpc_endpoint_id
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConflictException':
            # If the VPC endpoint already exists, retrieve it
            existing_endpoints = ec2.describe_vpc_endpoints(
                Filters=[
                    {'Name': 'vpc-id', 'Values': [vpc_id]},
                    {'Name': 'service-name', 'Values': ['com.amazonaws.us-east-1.aoss']}  # Adjust region if necessary
                ]
            )['VpcEndpoints']

            if existing_endpoints:
                vpc_endpoint_id = existing_endpoints[0]['VpcEndpointId']
                print(f"Using existing VPC endpoint: {vpc_endpoint_id}")
                return vpc_endpoint_id
            else:
                raise Exception("VPC endpoint conflict, but no existing endpoint found.")
        else:
            print(f"Error creating or getting network policy: {e.response['Error']['Message']}")
            raise

def create_data_access_policy(collection_name):
    policy_name = f"{collection_name}-data-access-policy"
    try:
        opensearch_serverless.create_access_policy(
            name=policy_name,
            policy=json.dumps([{
                "Rules": [{"ResourceType": "index", "Resource": [f"index/{collection_name}/*"]}],
                "Principal": ["*"],
                "Permission": ["aoss:*"]
            }]),
            type="data"
        )
        print(f"Data access policy created: {policy_name}")
    except ClientError as e:
        print(f"Error creating data access policy: {e.response['Error']['Message']}")
        raise

def create_collection(collection_name):
    try:
        response = opensearch_serverless.create_collection(
            name=collection_name,
            type='VECTORSEARCH',
            description='OpenSearch collection for Bedrock knowledge base'
        )
        collection_arn = response['createCollectionDetail']['arn']
        print(f"OpenSearch Serverless collection created: {collection_arn}")
        return collection_arn
    except ClientError as e:
        print(f"Error creating collection: {e.response['Error']['Message']}")
        raise

def wait_for_collection_active(collection_name):
    max_attempts = 60
    for attempt in range(max_attempts):
        try:
            response = opensearch_serverless.batch_get_collection(names=[collection_name])
            if response['collectionDetails'][0]['status'] == 'ACTIVE':
                print(f"Collection {collection_name} is now active")
                return
        except ClientError as e:
            print(f"Error checking collection status: {e.response['Error']['Message']}")
        time.sleep(10)
    raise Exception(f"Collection {collection_name} did not become active within the expected time")

def create_index(collection_name):
    try:
        endpoint = get_collection_endpoint(collection_name)
        # Here you would typically use the requests library to send a PUT request to create an index
        # For this example, we'll just print the instructions
        print(f"To create an index, send a PUT request to: https://{endpoint}/{collection_name}")
        print("With the following body:")
        print(json.dumps({
            "settings": {
                "index": {
                    "knn": True,
                    "knn.algo_param.ef_search": 512
                }
            },
            "mappings": {
                "properties": {
                    "bedrock_embedding": {
                        "type": "knn_vector",
                        "dimension": 1536,
                        "method": {
                            "name": "hnsw",
                            "space_type": "l2",
                            "engine": "nmslib",
                            "parameters": {
                                "ef_construction": 512,
                                "m": 16
                            }
                        }
                    },
                    "bedrock_text": {"type": "text"},
                    "bedrock_metadata": {"type": "object"}
                }
            }
        }, indent=2))
    except Exception as e:
        print(f"Error creating index: {str(e)}")
        raise

def get_collection_endpoint(collection_name):
    try:
        response = opensearch_serverless.batch_get_collection(names=[collection_name])
        return response['collectionDetails'][0]['collectionEndpoint']
    except ClientError as e:
        print(f"Error getting collection endpoint: {e.response['Error']['Message']}")
        raise