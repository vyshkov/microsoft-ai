import os
import sys
import json
from azure.identity import DefaultAzureCredential
from azure.cosmos import CosmosClient, exceptions

# Configuration
ENDPOINT = "https://vovy-cosmosdb.documents.azure.com:443/"
DATABASE_NAME = "agents-database"
CONTAINER_NAME = "agents-container"

def main():
    print(f"Connecting to Cosmos DB endpoint: {ENDPOINT}...")
    try:
        # 1. Initialize DefaultAzureCredential
        credential = DefaultAzureCredential()

        # 2. Initialize Cosmos Client
        client = CosmosClient(url=ENDPOINT, credential=credential)

        # 3. Access Database and Container
        database = client.get_database_client(DATABASE_NAME)
        container = database.get_container_client(CONTAINER_NAME)

        print(f"Fetching all items from container '{CONTAINER_NAME}' in database '{DATABASE_NAME}'...\n")

        # 4. Query all items
        # We use SELECT * FROM c to retrieve all documents.
        # enable_cross_partition_query=True allows scanning across all partitions.
        query = "SELECT * FROM c"
        items = container.query_items(
            query=query,
            enable_cross_partition_query=True
        )

        # 5. Print the retrieved items
        item_list = list(items)
        if not item_list:
            print("No items found in the collection.")
        else:
            print(f"Found {len(item_list)} items:")
            for index, item in enumerate(item_list, start=1):
                print(f"\n--- Item #{index} ---")
                # Format print only the relevant fields, avoiding system fields (like _rid, _self, etc.)
                user_fields = {k: v for k, v in item.items() if not k.startswith('_')}
                print(json.dumps(user_fields, indent=2))

        print("\nRead operation completed successfully!")

    except exceptions.CosmosHttpResponseError as e:
        print(f"\nCosmos DB HTTP Error occurred: {e.message}", file=sys.stderr)
    except Exception as e:
        print(f"\nAn error occurred: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
