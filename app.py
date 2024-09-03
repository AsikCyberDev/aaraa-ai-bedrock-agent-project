#!/usr/bin/env python3
import aws_cdk as cdk
from bedrock_agent_project.stacks.database_stack import DatabaseStack
from bedrock_agent_project.stacks.lambda_stack import LambdaStack
from bedrock_agent_project.stacks.state_machine_stack import StateMachineStack
from bedrock_agent_project.stacks.websocket_api_stack import WebSocketApiStack
from bedrock_agent_project.stacks.event_bridge_stack import EventBridgeStack
from bedrock_agent_project.stacks.custom_resource_stack import CustomResourceStack

app = cdk.App()

# Create stacks
database_stack = DatabaseStack(app, "DatabaseStack")
lambda_stack = LambdaStack(app, "LambdaStack", database_stack.chatbot_table, database_stack.agent_table)
# The StateMachineStack now includes steps for OpenSearch collection creation and status checking
state_machine_stack = StateMachineStack(app, "StateMachineStack", lambda_stack.functions)
websocket_api_stack = WebSocketApiStack(app, "WebSocketApiStack", lambda_stack.functions["invoke_agent"])
event_bridge_stack = EventBridgeStack(app, "EventBridgeStack", lambda_stack.functions["trigger_creation"])

# Create CustomResourceStack to update Lambda environment variables
custom_resource_stack = CustomResourceStack(
    app, "CustomResourceStack",
    lambda_functions=lambda_stack.functions,
    state_machine_arn=state_machine_stack.state_machine.state_machine_arn,
    websocket_url=websocket_api_stack.stage.url
)

# Add dependencies to ensure correct order of creation
custom_resource_stack.add_dependency(lambda_stack)
custom_resource_stack.add_dependency(state_machine_stack)
custom_resource_stack.add_dependency(websocket_api_stack)

app.synth()