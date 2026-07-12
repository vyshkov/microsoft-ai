import azure.functions as func
import logging
import json
from tasks_repository import TasksRepository

# Initialize the Function App
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# Create a single instance of TasksRepository to share connection pool
try:
    repo = TasksRepository()
    logging.info("Successfully connected TasksRepository to Cosmos DB.")
except Exception as e:
    logging.error(f"Failed to initialize TasksRepository: {e}")
    # In case initialization fails, we initialize it as None and try to reconnect on demand or raise errors.
    repo = None

@app.route(route="tasks", methods=["GET"])
def get_tasks(req: func.HttpRequest) -> func.HttpResponse:
    """Retrieve all current tasks from Cosmos DB."""
    logging.info("HTTP trigger - GET /api/tasks 2")
    if not repo:
        return func.HttpResponse(
            body=json.dumps({"error": "Cosmos DB connection is not initialized."}),
            mimetype="application/json",
            status_code=500
        )
    
    tasks = repo.get_all_tasks()
    return func.HttpResponse(
        body=json.dumps(tasks),
        mimetype="application/json",
        status_code=200
    )

@app.route(route="tasks", methods=["POST"])
def create_task(req: func.HttpRequest) -> func.HttpResponse:
    """Create a new task in Cosmos DB."""
    logging.info("HTTP trigger - POST /api/tasks")
    if not repo:
        return func.HttpResponse(
            body=json.dumps({"error": "Cosmos DB connection is not initialized."}),
            mimetype="application/json",
            status_code=500
        )
    
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
    
    try:
        new_task = repo.create_task(title=title, description=description)
        return func.HttpResponse(
            body=json.dumps(new_task),
            mimetype="application/json",
            status_code=201
        )
    except Exception as e:
        logging.error(f"Error creating task: {e}")
        return func.HttpResponse(
            body=json.dumps({"error": f"Failed to create task: {str(e)}"}),
            mimetype="application/json",
            status_code=500
        )

@app.route(route="tasks/{id}", methods=["PUT"])
def update_task(req: func.HttpRequest) -> func.HttpResponse:
    """Update an existing task in Cosmos DB."""
    task_id = req.route_params.get("id")
    logging.info(f"HTTP trigger - PUT /api/tasks/{task_id}")
    if not repo:
        return func.HttpResponse(
            body=json.dumps({"error": "Cosmos DB connection is not initialized."}),
            mimetype="application/json",
            status_code=500
        )
    
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
    completed = req_body.get("completed", False)
    
    # Ensure completed is a boolean
    if not isinstance(completed, bool):
        return func.HttpResponse(
            body=json.dumps({"error": "Field 'completed' must be a boolean"}),
            mimetype="application/json",
            status_code=400
        )
    
    try:
        updated_task = repo.update_task(
            task_id=task_id,
            title=title,
            description=description,
            completed=completed
        )
        
        if updated_task:
            return func.HttpResponse(
                body=json.dumps(updated_task),
                mimetype="application/json",
                status_code=200
            )
        else:
            return func.HttpResponse(
                body=json.dumps({"error": f"Task with ID {task_id} not found"}),
                mimetype="application/json",
                status_code=404
            )
    except Exception as e:
        logging.error(f"Error updating task: {e}")
        return func.HttpResponse(
            body=json.dumps({"error": f"Failed to update task: {str(e)}"}),
            mimetype="application/json",
            status_code=500
        )

@app.route(route="tasks/{id}", methods=["DELETE"])
def delete_task(req: func.HttpRequest) -> func.HttpResponse:
    """Delete a task by ID from Cosmos DB."""
    task_id = req.route_params.get("id")
    logging.info(f"HTTP trigger - DELETE /api/tasks/{task_id}")
    if not repo:
        return func.HttpResponse(
            body=json.dumps({"error": "Cosmos DB connection is not initialized."}),
            mimetype="application/json",
            status_code=500
        )
    
    try:
        success = repo.delete_task(task_id=task_id)
        if success:
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
    except Exception as e:
        logging.error(f"Error deleting task: {e}")
        return func.HttpResponse(
            body=json.dumps({"error": f"Failed to delete task: {str(e)}"}),
            mimetype="application/json",
            status_code=500
        )
