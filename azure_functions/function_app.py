import azure.functions as func
import logging
import json
import uuid

# Initialize the Function App with Anonymous auth level for ease of local testing and agent tool triggering
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# In-memory database of tasks for demonstration purposes
# Resetting the Function App will reset this memory, which is perfect for demonstration
TASKS_DB = [
    {
        "id": "1",
        "title": "Setup local environment",
        "description": "Install Azure Functions Core Tools and project dependencies.",
        "completed": True
    },
    {
        "id": "2",
        "title": "Configure agent OpenAPI tool",
        "description": "Import openapi.json into the Azure AI Foundry agent setup.",
        "completed": False
    }
]

@app.route(route="tasks", methods=["GET"])
def get_tasks(req: func.HttpRequest) -> func.HttpResponse:
    """Retrieve all current tasks."""
    logging.info("Retrieving task list.")
    return func.HttpResponse(
        body=json.dumps(TASKS_DB),
        mimetype="application/json",
        status_code=200
    )

@app.route(route="tasks", methods=["POST"])
def create_task(req: func.HttpRequest) -> func.HttpResponse:
    """Create a new task."""
    logging.info("Creating a new task.")
    try:
        req_body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            body=json.dumps({"error": "Invalid JSON body"}),
            mimetype="application/json",
            status_code=400
        )
    
    title = req_body.get("title")
    if not title:
        return func.HttpResponse(
            body=json.dumps({"error": "Missing required field: 'title'"}),
            mimetype="application/json",
            status_code=400
        )
    
    description = req_body.get("description", "")
    
    new_task = {
        "id": str(uuid.uuid4())[:8],  # A short unique identifier
        "title": title,
        "description": description,
        "completed": False
    }
    
    TASKS_DB.append(new_task)
    
    return func.HttpResponse(
        body=json.dumps(new_task),
        mimetype="application/json",
        status_code=201
    )

@app.route(route="tasks/{id}", methods=["DELETE"])
def delete_task(req: func.HttpRequest) -> func.HttpResponse:
    """Delete a task by its ID."""
    task_id = req.route_params.get("id")
    logging.info(f"Attempting to delete task ID: {task_id}")
    
    global TASKS_DB
    initial_length = len(TASKS_DB)
    TASKS_DB = [task for task in TASKS_DB if task["id"] != task_id]
    
    if len(TASKS_DB) < initial_length:
        return func.HttpResponse(
            body=json.dumps({"message": f"Task {task_id} successfully deleted"}),
            mimetype="application/json",
            status_code=200
        )
    else:
        return func.HttpResponse(
            body=json.dumps({"error": f"Task with ID {task_id} not found"}),
            mimetype="application/json",
            status_code=404
        )
