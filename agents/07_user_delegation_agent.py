import os
import sys
import json
import requests
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition, FunctionTool

# Add the project root to sys.path so 'utils' package is importable at runtime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.auth_helper import get_user_tokens_via_msal

# Reconfigure stdout to use UTF-8 on Windows console to prevent encoding crashes
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

load_dotenv()

# Configuration
PROJECT_ENDPOINT = os.environ.get("PROJECT_ENDPOINT", "https://vovyaz-test-foundry-1.services.ai.azure.com/api/projects/proj-default")
CLIENT_ID = os.environ.get("AZURE_CLIENT_ID", "d66fe946-550a-4048-9582-432a5ae95561")
TENANT_ID = os.environ.get("AZURE_TENANT_ID", "060e0979-b29c-46cc-9075-0c0478bffd3e")
FUNCTION_URL = "https://vovy-rest-api-bxchc2abe3htegc6.eastus-01.azurewebsites.net/api/tasks"

# 1. Authenticate the user interactively (Acquire User Token with roles claim)
print("=== Step 1: User Login ===")
try:
    auth_data = get_user_tokens_via_msal(CLIENT_ID, TENANT_ID, "access_as_user")
    USER_TOKEN = auth_data.get("id_token")
    if not USER_TOKEN:
        raise ValueError("Could not retrieve ID token.")
    print("User authenticated successfully via browser!\n")
except Exception as e:
    print(f"Authentication failed: {e}")
    sys.exit(1)

# 2. Define the local tool function that calls the API on behalf of the user
def execute_manage_tasks(action: str, task_title: str = None, task_id: str = None, completed: bool = None) -> str:
    """Execute the manage_tasks tool call locally, forwarding the user's token."""
    print(f"\n[Tool Execution] Calling Tasks API on behalf of user (Action: {action})...")
    headers = {
        "Authorization": f"Bearer {USER_TOKEN}",
        "Accept": "application/json"
    }

    try:
        if action == "list":
            res = requests.get(FUNCTION_URL, headers=headers)
        elif action == "create":
            if not task_title:
                return json.dumps({"error": "task_title is required for create action."})
            res = requests.post(FUNCTION_URL, headers=headers, json={"title": task_title})
        elif action == "update":
            if not task_id:
                return json.dumps({"error": "task_id is required for update action."})
            body = {}
            if task_title is not None:
                body["title"] = task_title
            if completed is not None:
                body["completed"] = completed
            res = requests.put(f"{FUNCTION_URL}/{task_id}", headers=headers, json=body)
        elif action == "delete":
            if not task_id:
                return json.dumps({"error": "task_id is required for delete action."})
            res = requests.delete(f"{FUNCTION_URL}/{task_id}", headers=headers)
        else:
            return json.dumps({"error": f"Unknown action '{action}'."})

        if res.status_code == 401:
            return json.dumps({"error": "Unauthenticated. The user token is invalid or expired."})
        elif res.status_code == 403:
            return json.dumps({"error": "Access Denied. The user does not have the required 'User' role."})

        return res.text
    except Exception as e:
        return json.dumps({"error": f"Connection error: {str(e)}"})

# 3. Define the FunctionTool with a JSON schema
tasks_tool = FunctionTool(
    name="manage_tasks",
    description="Query, create, update, or delete tasks in the task manager database on behalf of the user.",
    parameters={
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["list", "create", "update", "delete"],
                "description": "The action to perform: 'list' to get all tasks, 'create' to add a new task, 'update' to modify a task, 'delete' to remove a task."
            },
            "task_title": {
                "type": ["string", "null"],
                "description": "The title of the task. Required when action is 'create'. Optional for 'update'."
            },
            "task_id": {
                "type": ["string", "null"],
                "description": "The ID of the task. Required when action is 'update' or 'delete'."
            },
            "completed": {
                "type": ["boolean", "null"],
                "description": "Whether the task is completed. Used with 'update' action."
            }
        },
        "required": ["action", "task_title", "task_id", "completed"],
        "additionalProperties": False
    },
    strict=True
)

# 4. Initialize AIProjectClient
print("=== Step 2: Initializing AIProjectClient ===")
project_client = AIProjectClient(
    endpoint=PROJECT_ENDPOINT,
    credential=DefaultAzureCredential(),
)

agent_name = "07-user-delegation-agent"

# 5. Create the Agent with the Function Tool definition
print(f"Creating agent: {agent_name}...")
agent = project_client.agents.create_version(
    agent_name=agent_name,
    definition=PromptAgentDefinition(
        model="gpt-4o-mini",
        instructions=(
            "You are a helpful personal assistant with access to a task manager database. "
            "Help the user manage their tasks by listing, creating, or deleting them using the manage_tasks tool. "
            "If the tool returns an access denied or authorization error, explain clearly to the user "
            "that they lack the necessary permissions ('User' role) to perform that operation."
        ),
        tools=[tasks_tool]
    )
)
print(f"Agent {agent.name} (version {agent.version}) created.")

try:
    # 6. Use the OpenAI Responses API (same pattern as 01_get_agent_send_prompt.py)
    openai_client = project_client.get_openai_client()

    prompt = "Please add one more task to buy milk and then show all my tasks"
    print(f"\n=== Step 3: Prompting Agent: '{prompt}' ===")

    response = openai_client.responses.create(
        input=[{"role": "user", "content": prompt}],
        extra_body={"agent_reference": {"name": agent.name, "version": agent.version, "type": "agent_reference"}},
    )

    # 7. Handle tool calls in a loop until the agent produces a final text response
    max_iterations = 10
    iteration = 0

    while iteration < max_iterations:
        iteration += 1

        # Check if there are any function_call items in the response output
        tool_calls = [item for item in response.output if item.type == "function_call"]

        if not tool_calls:
            # No tool calls - the agent has produced its final answer
            break

        # Execute each tool call locally on behalf of the user
        tool_results = []
        for tool_call in tool_calls:
            print(f"\n[Agent requested tool call] {tool_call.name}({tool_call.arguments})")
            args = json.loads(tool_call.arguments)

            result = execute_manage_tasks(
                action=args.get("action"),
                task_title=args.get("task_title"),
                task_id=args.get("task_id"),
                completed=args.get("completed")
            )
            print(f"[Tool Result] {result[:200]}...")

            tool_results.append({
                "type": "function_call_output",
                "call_id": tool_call.call_id,
                "output": result
            })

        # Send the tool results back to the agent for the next turn
        response = openai_client.responses.create(
            input=tool_results,
            extra_body={"agent_reference": {"name": agent.name, "version": agent.version, "type": "agent_reference"}},
            previous_response_id=response.id,
        )

    # 8. Print the final agent response
    print(f"\nAgent Response:\n{response.output_text}")

finally:
    # Cleanup
    print("\n=== Step 4: Cleaning up resources ===")
    try:
        project_client.agents.delete(agent_name=agent_name)
        print(f"Deleted Agent: {agent_name}")
    except Exception as e:
        print(f"Error deleting Agent: {e}")
