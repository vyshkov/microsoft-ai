import os
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition

# Base configurations from 02_multi_agent_interaction.py
endpoint = "https://vovyaz-test-foundry-1.services.ai.azure.com/api/projects/proj-default"

print("Initializing AIProjectClient...")
project_client = AIProjectClient(
    endpoint=endpoint,
    credential=DefaultAzureCredential(),
)

# Define unique agent names for this script
agent_writer_name = "03-math-jokes-writer"
agent_critic_name = "03-joke-critic"

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
    # 1. Ask the Writer agent to generate a joke
    joke_prompt = "Write a joke about algebra."
    print(f"\n--- Prompting Agent 1 (Writer): '{joke_prompt}' ---")
    
    # Create thread for Writer
    thread_writer = project_client.agents.create_thread()
    
    # Add prompt as a message to the thread
    project_client.agents.create_message(
        thread_id=thread_writer.id,
        role="user",
        content=joke_prompt
    )
    
    # Run the agent on the thread and wait for completion
    run_writer = project_client.agents.create_and_process_run(
        thread_id=thread_writer.id,
        assistant_id=agent_writer.id
    )
    
    if run_writer.status == "completed":
        # Get messages from the thread
        messages_writer = project_client.agents.list_messages(thread_id=thread_writer.id)
        
        # Get the latest message (first in data list)
        joke = ""
        if messages_writer.data:
            latest_msg = messages_writer.data[0]
            for content_part in latest_msg.content:
                if content_part.type == "text":
                    joke = content_part.text.value
                    break
        print(f"Agent 1 Response:\n{joke}")
    else:
        print(f"Writer run failed with status: {run_writer.status}")
        joke = None

    # 2. Pass the joke to the Critic agent for analysis
    if joke:
        critique_prompt = f"Critique this math joke: {joke}"
        print(f"\n--- Prompting Agent 2 (Critic) with Agent 1's response ---")
        
        # Create thread for Critic
        thread_critic = project_client.agents.create_thread()
        
        # Add prompt as a message to the thread
        project_client.agents.create_message(
            thread_id=thread_critic.id,
            role="user",
            content=critique_prompt
        )
        
        # Run the critic agent on the thread and wait for completion
        run_critic = project_client.agents.create_and_process_run(
            thread_id=thread_critic.id,
            assistant_id=agent_critic.id
        )
        
        if run_critic.status == "completed":
            messages_critic = project_client.agents.list_messages(thread_id=thread_critic.id)
            critique = ""
            if messages_critic.data:
                latest_msg = messages_critic.data[0]
                for content_part in latest_msg.content:
                    if content_part.type == "text":
                        critique = content_part.text.value
                        break
            print(f"Agent 2 Response:\n{critique}")
        else:
            print(f"Critic run failed with status: {run_critic.status}")

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
