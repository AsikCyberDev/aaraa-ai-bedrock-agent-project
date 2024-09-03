import aws_cdk as cdk
from aws_cdk import custom_resources as cr
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_iam as iam
from constructs import Construct

class CustomResourceStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, lambda_functions: dict, state_machine_arn: str, websocket_url: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        update_lambda_function = lambda_.Function(
            self, "UpdateLambdaFunction",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="index.handler",
            code=lambda_.Code.from_asset("lambda/update_lambda"),
            timeout=cdk.Duration.minutes(5),
        )

        # Grant permissions to update Lambda functions
        update_lambda_function.add_to_role_policy(iam.PolicyStatement(
            actions=["lambda:UpdateFunctionConfiguration"],
            resources=[function.function_arn for function in lambda_functions.values()]
        ))

        cr.AwsCustomResource(
            self, "UpdateLambdaEnvironments",
            on_create=cr.AwsSdkCall(
                service="Lambda",
                action="updateFunctionConfiguration",
                parameters={
                    "FunctionName": update_lambda_function.function_name,
                    "Environment": {
                        "Variables": {
                            "LAMBDA_FUNCTIONS": ",".join(func.function_name for func in lambda_functions.values()),
                            "STATE_MACHINE_ARN": state_machine_arn,
                            "WEBSOCKET_URL": websocket_url
                        }
                    }
                },
                physical_resource_id=cr.PhysicalResourceId.of("UpdateLambdaEnvironments")
            ),
            policy=cr.AwsCustomResourcePolicy.from_sdk_calls(
                resources=cr.AwsCustomResourcePolicy.ANY_RESOURCE
            )
        )