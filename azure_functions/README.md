# Azure Function Task Manager (Agent OpenAPI Tool)

This directory contains a simple Azure Function built using the **Python v2 programming model**. It exposes a Task Manager REST API and includes a corresponding **OpenAPI 3.0 specification** (`openapi.json`). 

You can use this API as a tool for your Azure AI Foundry agents, allowing them to list, create, and delete tasks dynamically.

---

## File Structure

- `function_app.py`: The entry point implementing the HTTP routes.
- `openapi.json`: The OpenAPI 3.0.0 specification defining the API operations (`getTasks`, `createTask`, `deleteTask`).
- `host.json` & `local.settings.json`: Configuration files for the Azure Functions runtime.
- `requirements.txt`: Python package dependencies.

---

## Prerequisites

1. **Azure Functions Core Tools**:
   Install Azure Functions Core Tools to run the functions locally:
   - **Windows (Chocolatey)**: `choco install azure-functions-core-tools`
   - **Windows (npm)**: `npm install -g azure-functions-core-tools`
   - **macOS (Homebrew)**: `brew tap azure/functions && brew install azure-functions-core-tools`
2. **Python**:
   Since your project workspace is running Python 3.14.6, and Azure Functions supports up to **Python 3.13**, we recommend using Python 3.13 (or a virtual environment configured with a supported Python version like 3.10 to 3.13) to run the `func` host locally.

---

## Run Locally

1. Open a terminal and navigate to this directory:
   ```bash
   cd azure_functions
   ```
2. Initialize and activate a Python virtual environment (using Python 3.13 or another supported version):
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Start the Azure Functions host:
   ```bash
   func start
   ```

By default, the function app runs at `http://localhost:7071` and exposes the API routes under `/api`.

---

## Testing the API

You can test the endpoints manually using `curl` or any API client:

### 1. List Tasks (GET `/api/tasks`)
```bash
curl http://localhost:7071/api/tasks
```
**Response**:
```json
[
  {
    "id": "1",
    "title": "Setup local environment",
    "description": "Install Azure Functions Core Tools and project dependencies.",
    "completed": true
  },
  {
    "id": "2",
    "title": "Configure agent OpenAPI tool",
    "description": "Import openapi.json into the Azure AI Foundry agent setup.",
    "completed": false
  }
}
```

### 2. Create a Task (POST `/api/tasks`)
```bash
curl -X POST http://localhost:7071/api/tasks \
     -H "Content-Type: application/json" \
     -d '{"title": "Verify OpenAPI Tool", "description": "Ensure the agent invokes the local Azure Function."}'
```

### 3. Delete a Task (DELETE `/api/tasks/{id}`)
```bash
curl -X DELETE http://localhost:7071/api/tasks/1
```

---

## Registering with Azure AI Agents (OpenAPI Tool)

Below is an example snippet showing how you can load the `openapi.json` file in your Python agent script and register it as an `OpenApiTool` using the `azure-ai-projects` SDK:

```python
import os
import json
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import OpenApiTool, ConnectionAuth

# Initialize project client
endpoint = os.environ.get("PROJECT_ENDPOINT", "https://your-foundry-endpoint.services.ai.azure.com/api/projects/proj-default")
project_client = AIProjectClient(
    endpoint=endpoint,
    credential=DefaultAzureCredential(),
)

# Load the OpenAPI specification
openapi_path = os.path.join("azure_functions", "openapi.json")
with open(openapi_path, "r") as f:
    openapi_spec = json.load(f)

# Define the OpenAPI tool.
# Since the function runs locally, we authenticate using anonymous/no authentication for the local development server.
# Note: For production APIs, you can configure API Key or Entra ID connection authentication.
openapi_tool = OpenApiTool(
    name="task_manager_api",
    description="Allows listing, creating, and deleting tasks in the task tracker.",
    spec=openapi_spec,
    auth=ConnectionAuth(type="anonymous")
)

# Create the agent with the tool attached
agent = project_client.agents.create_version(
    agent_name="task-manager-agent",
    model="gpt-4o-mini",
    instructions=(
        "You are an assistant with access to a Task Manager. "
        "Help the user manage their tasks by listing, creating, or deleting them as requested. "
        "Always call the appropriate task manager tool when asked to modify or view tasks."
    ),
    tools=[openapi_tool]
)

print(f"Created Agent {agent.name} with OpenAPI Tool successfully.")
```
