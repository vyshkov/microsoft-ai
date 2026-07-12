import os
import sys
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

# Reconfigure stdout to use UTF-8 on Windows console to prevent encoding crashes
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

load_dotenv()

# Configuration
endpoint = os.environ.get("PROJECT_ENDPOINT", "https://vovyaz-test-foundry-1.services.ai.azure.com/api/projects/proj-default")
ai_search_index_name = "my-rag-ai-search-index-1"
ai_search_connection_id = "/subscriptions/40a7965b-275f-4e70-9e76-1ff9b2b40490/resourceGroups/foundry-test1/providers/Microsoft.CognitiveServices/accounts/vovyaz-test-foundry-1/projects/proj-default/connections/vovyaiseachj9kdyn"

print("Initializing AIProjectClient...")
project_client = AIProjectClient(
    endpoint=endpoint,
    credential=DefaultAzureCredential(),
)
openai_client = project_client.get_openai_client()

# Define Azure AI Search tool for the agent
search_resource = AzureAISearchToolResource(
    indexes=[
        AISearchIndexResource(
            project_connection_id=ai_search_connection_id,
            index_name=ai_search_index_name,
            query_type=AzureAISearchQueryType.SIMPLE,
        )
    ]
)
search_tool = AzureAISearchTool(azure_ai_search=search_resource)

agent_name = "05-agentic-rag-agent"

print(f"Creating agent: {agent_name}...")
agent = project_client.agents.create_version(
    agent_name=agent_name,
    definition=PromptAgentDefinition(
        model="gpt-4o-mini",
        instructions=(
            "You are a helpful customer support agent. "
            "Use the search tool to find relevant information and answer the user's questions. "
            "Always ground your responses in the retrieved documents."
        ),
        tools=[search_tool]
    )
)

def ask(question):
    print(f"\nCreating conversation for question: '{question}'...")
    
    # 1. Create a conversation
    conversation = openai_client.conversations.create()
    
    # 2. Generate response (the agent will invoke AzureAISearchTool automatically under the hood)
    response = openai_client.responses.create(
        conversation=conversation.id,
        input=question,
        extra_body={"agent_reference": {"name": agent_name, "type": "agent_reference"}},
    )
    
    return response.output_text

try:
    question = "Tell me about rich, creamy pistachio gelato from our search database."
    response_text = ask(question)
    print(f"\nAgent Response:\n{response_text}")
except Exception as e:
    print(f"\nExecution failed: {e}")
finally:
    # Cleanup
    print("\n--- Cleaning up resources ---")
    try:
        project_client.agents.delete(agent_name=agent_name)
        print(f"Deleted Agent: {agent_name}")
    except Exception as e:
        print(f"Error deleting Agent: {e}")

