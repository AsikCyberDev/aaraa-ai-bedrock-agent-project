
# File: stacks/websocket_api_stack.py

import aws_cdk as cdk
from aws_cdk import aws_apigatewayv2 as apigwv2
from aws_cdk import aws_apigatewayv2_integrations as integrations
from constructs import Construct

class WebSocketApiStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, invoke_agent_lambda, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.api = apigwv2.WebSocketApi(self, "BedrockAgentWebSocketApi")

        self.api.add_route(
            "$connect",
            integration=integrations.WebSocketLambdaIntegration(
                "ConnectIntegration",
                invoke_agent_lambda
            )
        )
        self.api.add_route(
            "$disconnect",
            integration=integrations.WebSocketLambdaIntegration(
                "DisconnectIntegration",
                invoke_agent_lambda
            )
        )
        self.api.add_route(
            "$default",
            integration=integrations.WebSocketLambdaIntegration(
                "DefaultIntegration",
                invoke_agent_lambda
            )
        )

        self.stage = apigwv2.WebSocketStage(
            self, "BedrockAgentWebSocketStage",
            web_socket_api=self.api,
            stage_name="prod",
            auto_deploy=True
        )