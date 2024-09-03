from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as lambda_,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    aws_ec2 as ec2,
)
from constructs import Construct

class LambdaStack(Stack):
    def __init__(self, scope: Construct, id: str, chatbot_table: dynamodb.Table, agent_table: dynamodb.Table, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Create a VPC
        self.vpc = ec2.Vpc(self, "BedrockVPC",
            max_azs=2,
            nat_gateways=1,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT,
                    cidr_mask=24
                )
            ]
        )

        # Create a security group for OpenSearch
        self.opensearch_sg = ec2.SecurityGroup(self, "OpenSearchSG",
            vpc=self.vpc,
            description="Security group for OpenSearch Serverless",
            allow_all_outbound=True
        )
        self.opensearch_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4(self.vpc.vpc_cidr_block),
            connection=ec2.Port.tcp(443),
            description="Allow HTTPS from VPC"
        )

        # Create an IAM role for the Bedrock Agent
        agent_role = iam.Role(self, "BedrockAgentRole",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com"),
            description="Role for Bedrock Agent to access necessary resources"
        )

        # Create an IAM role for the Knowledge Base
        knowledge_base_role = iam.Role(self, "KnowledgeBaseRole",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com"),
            description="Role for Knowledge Base to access necessary resources"
        )

        # Add necessary permissions to the agent role
        agent_role.add_to_policy(iam.PolicyStatement(
            actions=[
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:UpdateItem",
                "dynamodb:DeleteItem",
                "dynamodb:Query",
                "dynamodb:Scan"
            ],
            resources=[chatbot_table.table_arn, agent_table.table_arn]
        ))

        # Add necessary permissions to the knowledge base role
        knowledge_base_role.add_to_policy(iam.PolicyStatement(
            actions=[
                "aoss:APIAccessAll",
                "aoss:DescribeIndex",
                "aoss:CreateIndex",
                "aoss:DeleteIndex",
                "aoss:UpdateIndex",
                "aoss:DescribeCollection",
                "aoss:GetSecurityPolicy",
                "aoss:CreateSecurityPolicy",
                "aoss:UpdateSecurityPolicy",
                "aoss:BatchGetCollection",
                "aoss:CreateCollection",
                "aoss:DeleteCollection",
                "aoss:UpdateCollection",
                "aoss:ListCollections",
            ],
            resources=["*"]  # Scope this down to specific OpenSearch resources if possible
        ))

        self.functions = {}
        function_configs = [
            ("create_agent", "create_agent"),
            ("create_knowledge_base", "create_knowledge_base"),
            ("create_action_group", "create_action_group"),
            ("prepare_agent", "prepare_agent"),
            ("create_agent_alias", "create_agent_alias"),
            ("update_chatbot", "update_chatbot"),
            ("trigger_creation", "trigger_bedrock_agent_creation"),
            ("invoke_agent", "invoke_bedrock_agent"),
            ("create_opensearch_collection", "create_opensearch_collection"),
            ("check_collection_status", "check_collection_status"),
            ("associate_knowledge_base", "associate_knowledge_base"),
        ]

        # Define the ARN of your Step Functions state machine
        state_machine_arn = 'arn:aws:states:us-east-1:178115124427:stateMachine:BedrockAgentStateMachineE8A150FE-dZSAkl5o8j51'

        # Define the ARN of your embedding model (replace with the correct ARN)
        embedding_model_arn = 'arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v1'

        # Create a policy for Bedrock permissions
        bedrock_policy = iam.PolicyStatement(
            actions=[
                "bedrock:CreateAgent",
                "bedrock:CreateKnowledgeBase",
                "bedrock:CreateActionGroup",
                "bedrock:PrepareAgent",
                "bedrock:CreateAgentAlias",
                "bedrock:InvokeAgent",
                "bedrock:ListAgents",
                "bedrock:GetAgent",
                "bedrock:AssociateAgentKnowledgeBase",
                "bedrock:ListAgentVersions",
            ],
            resources=["*"]  # Scope this down to specific resources if possible
        )

        # Update the OpenSearch Serverless policy to include VPC endpoint and EC2 permissions
        opensearch_serverless_policy = iam.PolicyStatement(
            actions=[
                "aoss:CreateCollection",
                "aoss:DeleteCollection",
                "aoss:UpdateCollection",
                "aoss:ListCollections",
                "aoss:BatchGetCollection",
                "aoss:CreateSecurityPolicy",
                "aoss:GetSecurityPolicy",
                "aoss:ListSecurityPolicies",
                "aoss:UpdateSecurityPolicy",
                "aoss:DeleteSecurityPolicy",
                "aoss:CreateAccessPolicy",
                "aoss:GetAccessPolicy",
                "aoss:ListAccessPolicies",
                "aoss:UpdateAccessPolicy",
                "aoss:DeleteAccessPolicy",
                "aoss:DescribeIndex",
                "aoss:CreateIndex",
                "aoss:DeleteIndex",
                "aoss:UpdateIndex",
                "aoss:DescribeCollection",
                "aoss:CreateVpcEndpoint",
                "aoss:DeleteVpcEndpoint",
                "ec2:CreateVpcEndpoint",
                "ec2:DeleteVpcEndpoints",
                "ec2:DescribeVpcEndpoints",
                "ec2:ModifyVpcEndpoint",
                "ec2:DescribeVpcs",
                "ec2:DescribeSubnets",
                "ec2:DescribeSecurityGroups",
                "ec2:DescribeNetworkInterfaces",
                "ec2:CreateNetworkInterface",
                "ec2:DeleteNetworkInterface",
                "ec2:CreateTags",
                "ec2:DescribeTags",
                "ec2:DeleteTags",
            ],
            resources=["*"]  # Scope this down to specific resources if possible
        )


        lambda_list_functions_policy = iam.PolicyStatement(
            actions=["lambda:ListFunctions"],
            resources=["*"]
        )

        for function_id, directory_name in function_configs:
            function = lambda_.Function(
                self, f"{function_id.capitalize()}Lambda",
                runtime=lambda_.Runtime.PYTHON_3_9,
                handler="index.handler",
                code=lambda_.Code.from_asset(f"lambda/{directory_name}"),
                timeout=Duration.minutes(5),
                memory_size=256,
                environment={
                    'CHATBOT_TABLE_NAME': chatbot_table.table_name,
                    'AGENT_TABLE_NAME': agent_table.table_name,
                    'STATE_MACHINE_ARN': state_machine_arn,
                    'AGENT_ROLE_ARN': agent_role.role_arn,
                    'KNOWLEDGE_BASE_ROLE_ARN': knowledge_base_role.role_arn,
                    'EMBEDDING_MODEL_ARN': embedding_model_arn,
                    'VPC_ID': self.vpc.vpc_id,
                    'SUBNET_IDS': ','.join([subnet.subnet_id for subnet in self.vpc.private_subnets]),
                    'SECURITY_GROUP_ID': self.opensearch_sg.security_group_id,
                },
                vpc=self.vpc,
                vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT)
            )

            # Grant permissions
            chatbot_table.grant_read_write_data(function)
            agent_table.grant_read_write_data(function)
            function.add_to_role_policy(iam.PolicyStatement(
                actions=["states:StartExecution"],
                resources=[state_machine_arn]
            ))
            function.add_to_role_policy(bedrock_policy)
            function.add_to_role_policy(opensearch_serverless_policy)
            function.add_to_role_policy(lambda_list_functions_policy)
            function.add_to_role_policy(iam.PolicyStatement(
                actions=["iam:PassRole"],
                resources=[agent_role.role_arn, knowledge_base_role.role_arn]
            ))

            self.functions[function_id] = function

        # Print the table names and role ARNs for verification
        print(f"Chatbot Table Name: {chatbot_table.table_name}")
        print(f"Agent Table Name: {agent_table.table_name}")
        print(f"Agent Role ARN: {agent_role.role_arn}")
        print(f"Knowledge Base Role ARN: {knowledge_base_role.role_arn}")