import boto3
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)

class BedrockAgentWrapper:
    """Encapsulates Amazon Bedrock Agent actions."""

    def __init__(self, bedrock_agent_client):
        """
        :param bedrock_agent_client: A Boto3 Bedrock Agent client.
        """
        self.bedrock_agent_client = bedrock_agent_client

    def create_agent(self, agent_name, instruction, foundation_model, role_arn):
        """
        Creates an agent that orchestrates interactions between foundation models,
        data sources, software applications, user conversations, and APIs to carry
        out tasks to help customers.

        :param agent_name: A name for the agent.
        :param instruction: Instructions that tell the agent what it should do and how it should
                            interact with users.
        :param foundation_model: The foundation model to be used for orchestration by the agent.
        :param role_arn: The ARN of the IAM role with permissions needed by the agent.
        :return: The response from Agents for Bedrock if successful, otherwise raises an exception.
        """
        try:
            response = self.bedrock_agent_client.create_agent(
                agentName=agent_name,
                instruction=instruction,
                foundationModel=foundation_model,
                agentResourceRoleArn=role_arn,
            )
        except ClientError as e:
            logger.error(f"Error: Couldn't create agent. Here's why: {e}")
            raise
        else:
            return response['agent']

    def create_agent_action_group(self, name, description, agent_id, agent_version, function_arn, api_schema):
        """
        Creates an action group for an agent. An action group defines a set of actions that an
        agent should carry out for the customer.

        :param name: The name to give the action group.
        :param description: The description of the action group.
        :param agent_id: The unique identifier of the agent for which to create the action group.
        :param agent_version: The version of the agent for which to create the action group.
        :param function_arn: The ARN of the Lambda function containing the business logic that is
                             carried out upon invoking the action.
        :param api_schema: Contains the OpenAPI schema for the action group.
        :return: Details about the action group that was created.
        """
        try:
            response = self.bedrock_agent_client.create_agent_action_group(
                actionGroupName=name,
                description=description,
                agentId=agent_id,
                agentVersion=agent_version,
                actionGroupExecutor={"lambda": function_arn},
                apiSchema={"payload": api_schema},
            )
            agent_action_group = response['agentActionGroup']
        except ClientError as e:
            logger.error(f"Error: Couldn't create agent action group. Here's why: {e}")
            raise
        else:
            return agent_action_group

    def create_agent_alias(self, name, agent_id):
        """
        Creates an alias of an agent that can be used to deploy the agent.

        :param name: The name of the alias.
        :param agent_id: The unique identifier of the agent.
        :return: Details about the alias that was created.
        """
        try:
            response = self.bedrock_agent_client.create_agent_alias(
                agentAliasName=name,
                agentId=agent_id
            )
            agent_alias = response['agentAlias']
        except ClientError as e:
            logger.error(f"Couldn't create agent alias. {e}")
            raise
        else:
            return agent_alias

    def prepare_agent(self, agent_id):
        """
        Creates a DRAFT version of the agent that can be used for internal testing.

        :param agent_id: The unique identifier of the agent to prepare.
        :return: The response from Agents for Bedrock if successful, otherwise raises an exception.
        """
        try:
            prepared_agent_details = self.bedrock_agent_client.prepare_agent(agentId=agent_id)
        except ClientError as e:
            logger.error(f"Couldn't prepare agent. {e}")
            raise
        else:
            return prepared_agent_details

    def associate_agent_knowledge_base(self, agent_id, agent_version, knowledge_base_id, description):
        """
        Associates a knowledge base with an agent.

        :param agent_id: The ID of the agent.
        :param agent_version: The version of the agent.
        :param knowledge_base_id: The ID of the knowledge base to associate.
        :param description: A description of the association.
        :return: The response from Agents for Bedrock if successful, otherwise raises an exception.
        """
        try:
            response = self.bedrock_agent_client.associate_agent_knowledge_base(
                agentId=agent_id,
                agentVersion=agent_version,
                knowledgeBaseId=knowledge_base_id,
                description=description
            )
        except ClientError as e:
            logger.error(f"Couldn't associate knowledge base with agent. {e}")
            raise
        else:
            return response

    def invoke_agent(self, agent_id, agent_alias_id, session_id, input_text):
        """
        Invokes an agent with the given input.

        :param agent_id: The ID of the agent to invoke.
        :param agent_alias_id: The ID of the agent alias to use.
        :param session_id: A unique identifier for the session.
        :param input_text: The input text to send to the agent.
        :return: The response from the agent.
        """
        bedrock_runtime_client = boto3.client('bedrock-runtime')
        try:
            response = bedrock_runtime_client.invoke_agent(
                agentId=agent_id,
                agentAliasId=agent_alias_id,
                sessionId=session_id,
                inputText=input_text
            )
        except ClientError as e:
            logger.error(f"Couldn't invoke agent. {e}")
            raise
        else:
            return response