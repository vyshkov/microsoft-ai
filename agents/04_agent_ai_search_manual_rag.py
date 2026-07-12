import os
import sys
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition, ConnectionType
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizableTextQuery

# Reconfigure stdout to use UTF-8 on Windows console to prevent encoding crashes
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

load_dotenv()

# Configuration
endpoint = os.environ.get("PROJECT_ENDPOINT", "https://vovyaz-test-foundry-1.services.ai.azure.com/api/projects/proj-default")
ai_search_endpoint = "https://vovyaiseach.search.windows.net"
ai_search_index_name = "my-rag-ai-search-index-1"

print("Initializing AIProjectClient...")
project_client = AIProjectClient(
    endpoint=endpoint,
    credential=DefaultAzureCredential(),
)

# Retrieve search credentials
print("Retrieving AI Search connection credentials...")
search_connection = project_client.connections.get_default(
    connection_type=ConnectionType.AZURE_AI_SEARCH,
    include_credentials=True
)
api_key = search_connection.credentials.api_key

# Initialize SearchClient for manual retrieval
search_client = SearchClient(
    endpoint=ai_search_endpoint,
    credential=AzureKeyCredential(api_key),
    index_name=ai_search_index_name,
)

agent_name = "04-manual-rag-agent"

print(f"Creating agent: {agent_name}...")
agent = project_client.agents.create_version(
    agent_name=agent_name,
    definition=PromptAgentDefinition(
        model="gpt-4o-mini",
        instructions="You are a helpful customer support agent. Answer the question using ONLY the provided sources."
    )
)

def ask(question):
    # 1. Fetch relevant source chunks manually
    results = search_client.search(
        search_text=question,
        vector_queries=[
            VectorizableTextQuery(text=question, k_nearest_neighbors=3, fields="text_vector")
        ],
        select=["chunk", "title", "parent_id"],
        top=3,
    )

    source_list = []
    for result in results:
        title = result.get("title", "Unknown source")
        parent_id = result.get("parent_id", "")
        chunk = result.get("chunk", "")
        source_list.append(f"[Source title: {title}] (ID: {parent_id})\n{chunk}")
    
    sources = "\n\n".join(source_list)

    # 2. Build the grounded prompt
    prompt = f"""Answer the customer question using only the sources provided below.
If the sources do not contain enough information, say that the knowledge base does not contain enough information.

Sources:
{sources}

Customer question:
{question}"""

    print("\nPrompt sent to agent:\n", prompt)

    # 3. Call the agent with the injected prompt context
    openai_client = project_client.get_openai_client()
    response = openai_client.responses.create(
        extra_body={"agent_reference": {"name": agent_name, "type": "agent_reference"}},
        input=prompt,
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
