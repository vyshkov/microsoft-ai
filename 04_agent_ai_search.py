import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    PromptAgentDefinition,
    AzureAISearchTool,
    AzureAISearchToolResource,
    AISearchIndexResource,
    AzureAISearchQueryType
)

# Load environment variables from .env if present
load_dotenv()

# Base configuration
endpoint = os.environ.get("PROJECT_ENDPOINT", "https://vovyaz-test-foundry-1.services.ai.azure.com/api/projects/proj-default")

print("Initializing AIProjectClient...")
project_client = AIProjectClient(
    endpoint=endpoint,
    credential=DefaultAzureCredential(),
)

# 1. Configure the Azure AI Search connection ID and index name.
# You can set these in your environment or substitute your actual values below.
ai_search_connection_id = os.environ.get("AI_SEARCH_CONNECTION_ID")
ai_search_index_name = os.environ.get("AI_SEARCH_INDEX_NAME")

# Dynamic fallback: try to locate a CognitiveSearch connection name in the project automatically
if not ai_search_connection_id:
    print("Searching for an Azure AI Search connection in the project...")
    try:
        for conn in project_client.connections.list():
            if conn.type == "CognitiveSearch" or "search" in conn.name.lower():
                ai_search_connection_id = conn.id
                print(f"Found search connection: {conn.name} ({conn.id})")
                break
    except Exception as e:
        print(f"Could not list connections: {e}")

# Placeholders if no environment variables or active connections are found
if not ai_search_connection_id:
    ai_search_connection_id = "/subscriptions/your-sub/resourceGroups/your-rg/providers/Microsoft.CognitiveServices/accounts/your-account/projects/your-project/connections/your-search-connection"
    print(f"No active Search connection found. Using placeholder connection ID: {ai_search_connection_id}")

if not ai_search_index_name:
    ai_search_index_name = "your-search-index"
    print(f"No search index name provided. Using placeholder index name: {ai_search_index_name}")


# 2. Define the Azure AI Search tool using AzureAISearchToolResource and AISearchIndexResource
print("\nSetting up Azure AI Search tool...")
search_resource = AzureAISearchToolResource(
    indexes=[
        AISearchIndexResource(
            project_connection_id=ai_search_connection_id,
            index_name=ai_search_index_name,
            query_type=AzureAISearchQueryType.SIMPLE,  # Options include: SIMPLE, SEMANTIC, VECTOR, VECTOR_SIMPLE_HYBRID, VECTOR_SEMANTIC_HYBRID
        )
    ]
)
search_tool = AzureAISearchTool(azure_ai_search=search_resource)

# Define unique agent name for this script
agent_name = "04-ai-search-agent"

print(f"\nCreating agent: {agent_name}...")
agent = project_client.agents.create_version(
    agent_name=agent_name,
    definition=PromptAgentDefinition(
        model="gpt-4o-mini",
        instructions=(
            "You are a helpful customer support agent. "
            "Use the provided Azure AI Search tool to find relevant information "
            "and answer the user's questions. Always ground your responses in the retrieved documents."
        ),
        tools=[search_tool]
    )
)
print(f"Created Agent: {agent.name} (version {agent.version})")

try:
    # 3. Create a thread
    print("\nCreating agent conversation thread...")
    thread = project_client.agents.create_thread()
    print(f"Created thread: {thread.id}")

    # Define a grounding query and add it as a message to the thread
    prompt = "Tell me about the latest features or pricing plans from our search database."
    print(f"\n--- Adding message to thread: '{prompt}' ---")
    project_client.agents.create_message(
        thread_id=thread.id,
        role="user",
        content=prompt
    )

    # 4. Run the agent on the thread and wait for completion (model-agnostic execution)
    print("Running the agent...")
    run = project_client.agents.create_and_process_run(
        thread_id=thread.id,
        assistant_id=agent.id
    )
    print(f"Run status: {run.status}")

    if run.status == "completed":
        # Get messages from the thread
        messages = project_client.agents.list_messages(thread_id=thread.id)
        
        # Extract the latest response
        response_text = ""
        if messages.data:
            latest_msg = messages.data[0]
            for content_part in latest_msg.content:
                if content_part.type == "text":
                    response_text = content_part.text.value
                    break
        print(f"\nAgent Response:\n{response_text}")
    else:
        print(f"\nAgent execution failed with status: {run.status}")

except Exception as e:
    print(f"\nExecution failed: {e}")
    print("\n[NOTE] If the run failed, please verify that:")
    print("1. Your Azure AI Search service is connected to your Azure AI Foundry project.")
    print("2. The connection ID and index name are configured correctly in your environment variables or script.")

finally:
    # 5. Clean up the created agent
    print("\n--- Cleaning up resources ---")
    try:
        project_client.agents.delete(agent_name=agent_name)
        print(f"Deleted Agent: {agent_name}")
    except Exception as e:
        print(f"Error deleting Agent: {e}")
