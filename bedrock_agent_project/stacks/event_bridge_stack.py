

# File: stacks/event_bridge_stack.py

import aws_cdk as cdk
from aws_cdk import aws_events as events
from aws_cdk import aws_events_targets as targets
from constructs import Construct

class EventBridgeStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, trigger_creation_lambda, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        rule = events.Rule(
            self, "ChatbotCreatedRule",
            event_pattern=events.EventPattern(
                source=["com.myapp.chatbot"],
                detail_type=["ChatbotCreated"],
                detail={
                    "type": ["BEDROCK_AGENT"]
                }
            )
        )
        rule.add_target(targets.LambdaFunction(trigger_creation_lambda))