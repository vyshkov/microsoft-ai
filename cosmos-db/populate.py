import os
import sys
from azure.identity import DefaultAzureCredential
from azure.cosmos import CosmosClient, exceptions

# Configuration
ENDPOINT = "https://vovy-cosmosdb.documents.azure.com:443/"
DATABASE_NAME = "agents-database"
CONTAINER_NAME = "agents-container"

# Sample Todo List Items to populate
TODO_ITEMS = [
    {
        "id": "task-1",
        "title": "Complete Azure Function integration",
        "description": "Expose the function app endpoints for the AI Agent.",
        "category": "Development",
        "completed": False
    },
    {
        "id": "task-2",
        "title": "Configure Azure Cosmos DB container",
        "description": "Establish Tasks collection with partition key '/id'.",
        "category": "Database",
        "completed": True
    },
    {
        "id": "task-3",
        "title": "Register OpenAPI tool on Azure AI Agent",
        "description": "Upload the openapi.json file to the Azure AI Foundry portal.",
        "category": "Agent",
        "completed": False
    },
    {
        "id": "task-4",
        "title": "Verify end-to-end agentic workflow",
        "description": "Test that the agent can successfully query and modify data.",
        "category": "Testing",
        "completed": False
    }
]

def main():
    print(f"Connecting to Cosmos DB endpoint: {ENDPOINT}...")
    try:
        # 1. Initialize DefaultAzureCredential
        # DefaultAzureCredential will automatically pick up credentials from your environment:
        # e.g., Azure CLI session (via 'az login'), VS Code, or Azure Managed Identity.
        credential = DefaultAzureCredential()

        # 2. Initialize Cosmos Client
        client = CosmosClient(url=ENDPOINT, credential=credential)

        # 3. Create Database if not exists
        print(f"Ensuring database '{DATABASE_NAME}' exists...")
        database = client.create_database_if_not_exists(id=DATABASE_NAME)

        # 4. Create Container if not exists
        # We define '/id' as the partition key for this simple setup.
        print(f"Ensuring container '{CONTAINER_NAME}' exists...")
        container = database.create_container_if_not_exists(
            id=CONTAINER_NAME,
            partition_key={"path": "/id", "kind": "Hash"}
        )

        # 5. Populate/Upsert Items
        print("\nPopulating Todo List Data:")
        for item in TODO_ITEMS:
            print(f" -> Upserting task: {item['title']} ({item['id']})...")
            # Using upsert_item ensures we don't throw duplicate key errors if run multiple times
            container.upsert_item(body=item)

        print("\nSuccessfully populated Cosmos DB collection with Todo List data!")

    except exceptions.CosmosHttpResponseError as e:
        print(f"\nCosmos DB HTTP Error occurred: {e.message}", file=sys.stderr)
        print("Note: Please check if your identity has 'Azure Cosmos DB Built-in Data Contributor' Role-Based Access Control (RBAC) permissions on the Cosmos DB account.", file=sys.stderr)
    except Exception as e:
        print(f"\nAn error occurred: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
