import os
import uuid
from azure.identity import DefaultAzureCredential
from azure.cosmos import CosmosClient, exceptions

class TasksRepository:
    def __init__(self):
        # Configuration
        self.endpoint = os.environ.get("COSMOS_ENDPOINT", "https://vovy-cosmosdb.documents.azure.com:443/")
        self.database_name = os.environ.get("COSMOS_DATABASE", "agents-database")
        self.container_name = os.environ.get("COSMOS_CONTAINER", "agents-container")
        
        # Initialize Cosmos Client using DefaultAzureCredential
        self.credential = DefaultAzureCredential()
        self.client = CosmosClient(url=self.endpoint, credential=self.credential)
        
        # Access Database & Container
        self.database = self.client.get_database_client(self.database_name)
        self.container = self.database.get_container_client(self.container_name)

    def _clean_item(self, item: dict) -> dict:
        """Helper to remove Cosmos DB system metadata fields starting with underscore."""
        return {k: v for k, v in item.items() if not k.startswith('_')}

    def get_all_tasks(self) -> list:
        """Fetch all tasks from the container."""
        query = "SELECT * FROM c"
        try:
            items = self.container.query_items(
                query=query,
                enable_cross_partition_query=True
            )
            return [self._clean_item(item) for item in items]
        except exceptions.CosmosHttpResponseError:
            # Return empty list if query fails or container is missing/empty
            return []

    def get_task_by_id(self, task_id: str) -> dict:
        """Fetch a specific task by its ID."""
        try:
            item = self.container.read_item(item=task_id, partition_key=task_id)
            return self._clean_item(item)
        except exceptions.CosmosResourceNotFoundError:
            return None

    def create_task(self, title: str, description: str = "") -> dict:
        """Create and insert a new task."""
        task_id = str(uuid.uuid4())[:8]
        new_task = {
            "id": task_id,
            "title": title,
            "description": description,
            "completed": False
        }
        self.container.create_item(body=new_task)
        return new_task

    def update_task(self, task_id: str, title: str, description: str, completed: bool) -> dict:
        """Update/Replace an existing task."""
        try:
            # Read first to verify it exists
            existing_task = self.container.read_item(item=task_id, partition_key=task_id)
            
            existing_task["title"] = title
            existing_task["description"] = description
            existing_task["completed"] = completed
            
            self.container.replace_item(item=task_id, body=existing_task)
            return self._clean_item(existing_task)
        except exceptions.CosmosResourceNotFoundError:
            return None

    def delete_task(self, task_id: str) -> bool:
        """Delete a task by ID. Returns True if deleted, False if not found."""
        try:
            self.container.delete_item(item=task_id, partition_key=task_id)
            return True
        except exceptions.CosmosResourceNotFoundError:
            return False
