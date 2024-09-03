# File: app.py

import aws_cdk as cdk
from stacks.database_stack import DatabaseStack
from stacks.lambda_stack import LambdaStack
from stacks.state_machine_stack import StateMachineStack
from stacks.websocket_api_stack import WebSocketApiStack
from stacks.event_bridge_stack import EventBridgeStack
from aspects.lambda_environment_setter import LambdaEnvironmentSetter

app = cdk.App()

database_stack = DatabaseStack(app, "DatabaseStack")
lambda_stack = LambdaStack(app, "LambdaStack", database_stack.chatbot_table, database_stack.agent_table)
state_machine_stack = StateMachineStack(app, "StateMachineStack", lambda_stack.functions)
websocket_api_stack = WebSocketApiStack(app, "WebSocketApiStack", lambda_stack.functions["invoke_agent"])
event_bridge_stack = EventBridgeStack(app, "EventBridgeStack", lambda_stack.functions["trigger_creation"])

# Update Lambda environment variables
cdk.Aspects.of(lambda_stack).add(
    LambdaEnvironmentSetter(
        state_machine_arn=state_machine_stack.state_machine.state_machine_arn,
        websocket_url=websocket_api_stack.stage.url
    )
)

app.synth()
