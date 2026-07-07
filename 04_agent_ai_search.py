import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    PromptAgentDefinition,
    AzureAISearchTool,
    AzureAISearchToolResource,
    AISearchIndexResource,
    AzureAISearchQueryType,
    ConnectionType
)

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizableTextQuery

# Load environment variables from .env if present
load_dotenv()

# Base configuration
endpoint = os.environ.get("PROJECT_ENDPOINT", "https://vovyaz-test-foundry-1.services.ai.azure.com/api/projects/proj-default")

ai_search_endpoint = "https://vovyaiseach.search.windows.net"
ai_search_index_name = "my-rag-ai-search-index-1"
ai_search_connection_id = "/subscriptions/40a7965b-275f-4e70-9e76-1ff9b2b40490/resourceGroups/foundry-test1/providers/Microsoft.CognitiveServices/accounts/vovyaz-test-foundry-1/projects/proj-default/connections/vovyaiseachj9kdyn"

print("Initializing AIProjectClient...")
project_client = AIProjectClient(
    endpoint=endpoint,
    credential=DefaultAzureCredential(),
)

openai_client = project_client.get_openai_client()

# Dynamically retrieve connection key to resolve the Forbidden error for SearchClient
print("Retrieving AI Search connection credentials...")
search_connection = project_client.connections.get_default(
    connection_type=ConnectionType.AZURE_AI_SEARCH,
    include_credentials=True
)
api_key = search_connection.credentials.api_key

print("Initializing SearchClient with retrieved API Key...")
search_client = SearchClient(
    endpoint=ai_search_endpoint,
    credential=AzureKeyCredential(api_key),
    index_name=ai_search_index_name,
)

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
            "Use the provided sources to find relevant information "
            "and answer the user's questions. Always ground your responses in the retrieved documents."
        ),
        tools=[search_tool]
    )
)
print(f"Created Agent: {agent.name} (version {agent.version})")


def ask(question):
    # Step 1: Retrieve grounding data from Azure AI Search
    results = search_client.search(
        search_text=question,
        vector_queries=[
            VectorizableTextQuery(
                text=question,
                k_nearest_neighbors=3,
                fields="text_vector",
            )
        ],
        select=["chunk", "title", "parent_id"],
        top=3,
    )

    # Step 2: Convert search results into source text
    source_list = []

    for result in results:
        title = result.get("title", "Unknown source")
        parent_id = result.get("parent_id", "")
        chunk = result.get("chunk", "")

        source_text = f"""
[Source title: {title}]
[Parent ID: {parent_id}]
{chunk}
"""
        source_list.append(source_text)        

    sources = "\n\n".join(source_list)

    # Step 3: Build the grounded prompt for the agent
    prompt = f"""
You are a helpful customer support agent.

Answer the customer question using only the sources provided below.
If the sources do not contain enough information, say that the knowledge base does not contain enough information.

Sources:
{sources}

Customer question:
{question}
"""

    print("\nPrompt sent to agent:\n")
    print(prompt)

    # Step 4: Ask the Foundry agent to answer using the sources
    response = openai_client.responses.create(
        extra_body={
            "agent_reference": {
                "name": agent_name,
                "type": "agent_reference"
            }
        },
        input=prompt,
    )

    return response.output_text


try:
    question = "Tell me about rich, creamy pistachio gelato from our search database."
    response_text = ask(question)
    print(f"\nAgent Response:\n{response_text}")

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
