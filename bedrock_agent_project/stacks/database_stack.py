import aws_cdk as cdk
from aws_cdk import aws_dynamodb as dynamodb
from constructs import Construct

class DatabaseStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.chatbot_table = dynamodb.Table(
            self, "ChatbotTable",
            partition_key=dynamodb.Attribute(name="id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="projectId", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
        )

        self.agent_table = dynamodb.Table(
            self, "AgentTable",
            partition_key=dynamodb.Attribute(name="chatbotId", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
        )