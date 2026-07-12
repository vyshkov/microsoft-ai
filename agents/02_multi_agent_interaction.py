import os
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition

# Base configurations from 01_get_agent_send_prompt.py
endpoint = "https://vovyaz-test-foundry-1.services.ai.azure.com/api/projects/proj-default"

print("Initializing AIProjectClient...")
project_client = AIProjectClient(
    endpoint=endpoint,
    credential=DefaultAzureCredential(),
)

# Define unique agent names for this script
agent_writer_name = "02-math-jokes-writer"
agent_critic_name = "02-joke-critic"

print(f"Creating agent: {agent_writer_name}...")
agent_writer = project_client.agents.create_version(
    agent_name=agent_writer_name,
    definition=PromptAgentDefinition(
        model="gpt-4o-mini",
        instructions="You are a creative writer who writes short, funny jokes about mathematics. Only output the joke and nothing else."
    )
)
print(f"Created Agent 1: {agent_writer.name} (version {agent_writer.version})")

print(f"Creating agent: {agent_critic_name}...")
agent_critic = project_client.agents.create_version(
    agent_name=agent_critic_name,
    definition=PromptAgentDefinition(
        model="gpt-4o-mini",
        instructions="You are a critical reviewer. Analyze the math joke provided and explain why it is funny, or suggest how it could be improved."
    )
)
print(f"Created Agent 2: {agent_critic.name} (version {agent_critic.version})")

try:
    print("\nRetrieving OpenAI client...")
    openai_client = project_client.get_openai_client()

    # 1. Ask the Writer agent to generate a joke
    joke_prompt = "Write a joke about algebra."
    print(f"\n--- Prompting Agent 1 (Writer): '{joke_prompt}' ---")
    response_writer = openai_client.responses.create(
        input=[{"role": "user", "content": joke_prompt}],
        extra_body={
            "agent_reference": {
                "name": agent_writer.name,
                "version": agent_writer.version,
                "type": "agent_reference"
            }
        },
    )
    joke = response_writer.output_text
    print(f"Agent 1 Response:\n{joke}")

    # 2. Pass the joke to the Critic agent for analysis
    critique_prompt = f"Critique this math joke: {joke}"
    print(f"\n--- Prompting Agent 2 (Critic) with Agent 1's response ---")
    response_critic = openai_client.responses.create(
        input=[{"role": "user", "content": critique_prompt}],
        extra_body={
            "agent_reference": {
                "name": agent_critic.name,
                "version": agent_critic.version,
                "type": "agent_reference"
            }
        },
    )
    critique = response_critic.output_text
    print(f"Agent 2 Response:\n{critique}")

finally:
    # 3. Clean up the created agents
    print("\n--- Cleaning up resources ---")
    try:
        project_client.agents.delete(agent_name=agent_writer_name)
        print(f"Deleted Agent 1: {agent_writer_name}")
    except Exception as e:
        print(f"Error deleting Agent 1: {e}")

    try:
        project_client.agents.delete(agent_name=agent_critic_name)
        print(f"Deleted Agent 2: {agent_critic_name}")
    except Exception as e:
        print(f"Error deleting Agent 2: {e}")
