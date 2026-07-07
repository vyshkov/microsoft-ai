from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizableTextQuery

PROJECT_ENDPOINT = "https://foundry-dev-eus-01.services.ai.azure.com/api/projects/ai-103-project"
SEARCH_ENDPOINT = "https://cloudxeus-search01.search.windows.net"
INDEX_NAME = "rag-1782198581571"
AGENT_NAME = "cloudxeus-support-rag-agent"

project = AIProjectClient(
    endpoint=PROJECT_ENDPOINT,
    credential=DefaultAzureCredential()
)

openai_client = project.get_openai_client()

search_client = SearchClient(
    endpoint=SEARCH_ENDPOINT,
    index_name=INDEX_NAME,
    credential=DefaultAzureCredential(),
)


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
You are a customer support agent for CloudXeus Technology Services.

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
                "name": AGENT_NAME,
                "type": "agent_reference"
            }
        },
        input=prompt,
    )

    return response.output_text


print(ask("Can I get my money back?"))