import aws_cdk as cdk
from aws_cdk import aws_stepfunctions as sfn
from aws_cdk import aws_stepfunctions_tasks as tasks
from constructs import Construct

class StateMachineStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, lambda_functions: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create OpenSearch Collection
        create_opensearch_collection_task = tasks.LambdaInvoke(
            self, "Create OpenSearch Collection",
            lambda_function=lambda_functions["create_opensearch_collection"],
            result_path="$.opensearchCollection"
        )

        # Wait state for OpenSearch collection creation
        wait_for_collection = sfn.Wait(
            self, "Wait for Collection",
            time=sfn.WaitTime.duration(cdk.Duration.seconds(60))
        )

        # Check Collection Status
        check_collection_status_task = tasks.LambdaInvoke(
            self, "Check Collection Status",
            lambda_function=lambda_functions["check_collection_status"],
            result_path="$.collectionStatus"
        )

        # Choice state to check if collection is active
        is_collection_active = sfn.Choice(self, "Is Collection Active?")
        collection_not_active = sfn.Condition.string_equals("$.collectionStatus.Payload.status", "CREATING")

        # Create Bedrock Agent
        create_agent_task = tasks.LambdaInvoke(
            self, "Create Bedrock Agent",
            lambda_function=lambda_functions["create_agent"],
            result_path="$.createAgent"
        )

        # Create Knowledge Base
        create_knowledge_base_task = tasks.LambdaInvoke(
            self, "Create Knowledge Base",
            lambda_function=lambda_functions["create_knowledge_base"],
            result_path="$.knowledgeBase"
        )

        # Associate Knowledge Base
        associate_knowledge_base_task = tasks.LambdaInvoke(
            self, "Associate Knowledge Base",
            lambda_function=lambda_functions["associate_knowledge_base"],
            result_path="$.associateKnowledgeBase"
        )

        # Create Action Group
        create_action_group_task = tasks.LambdaInvoke(
            self, "Create Action Group",
            lambda_function=lambda_functions["create_action_group"],
            result_path="$.actionGroup"
        )

        # Prepare Agent
        prepare_agent_task = tasks.LambdaInvoke(
            self, "Prepare Agent",
            lambda_function=lambda_functions["prepare_agent"],
            result_path="$.prepareAgent"
        )

        # Create Agent Alias
        create_agent_alias_task = tasks.LambdaInvoke(
            self, "Create Agent Alias",
            lambda_function=lambda_functions["create_agent_alias"],
            result_path="$.agentAlias"
        )

        # Update Chatbot
        update_chatbot_task = tasks.LambdaInvoke(
            self, "Update Chatbot",
            lambda_function=lambda_functions["update_chatbot"],
            result_path="$.updateChatbot"
        )

        # Define the workflow
        definition = create_opensearch_collection_task.next(
            wait_for_collection
        ).next(
            check_collection_status_task
        ).next(
            is_collection_active
                .when(collection_not_active, wait_for_collection)
                .otherwise(
                    create_agent_task.next(
                        sfn.Parallel(self, "Create and Associate Knowledge Base and Create Action Group")
                        .branch(create_knowledge_base_task.next(associate_knowledge_base_task))
                        .branch(create_action_group_task)
                    ).next(prepare_agent_task)
                    .next(create_agent_alias_task)
                    .next(update_chatbot_task)
                )
        )

        # Create the state machine
        self.state_machine = sfn.StateMachine(
            self, "BedrockAgentStateMachine",
            definition_body=sfn.DefinitionBody.from_chainable(definition),
            timeout=cdk.Duration.minutes(30)
        )