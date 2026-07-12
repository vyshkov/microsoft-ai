import azure.functions as func
import logging
import json
import base64
from tasks_repository import TasksRepository

# Initialize the Function App
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# Create a single instance of TasksRepository to share connection pool
try:
    repo = TasksRepository()
    logging.info("Successfully connected TasksRepository to Cosmos DB.")
except Exception as e:
    logging.error(f"Failed to initialize TasksRepository: {e}")
    repo = None

def is_authorized(req: func.HttpRequest) -> tuple[bool, int, str]:
    """
    Checks authorization by verifying if the user has the 'User' role.
    Supports both Azure Easy Auth (via X-MS-CLIENT-PRINCIPAL header) and
    local client testing (via Bearer Authorization token fallback).
    
    :return: A tuple of (is_authorized_bool, http_status_code, error_message)
    """
    principal_header = req.headers.get("X-MS-CLIENT-PRINCIPAL")
    
    # 1. Easy Auth Path (Production)
    if principal_header:
        try:
            # Easy Auth forwards a base64 encoded JSON string in the X-MS-CLIENT-PRINCIPAL header
            decoded_bytes = base64.b64decode(principal_header)
            principal_data = json.loads(decoded_bytes.decode("utf-8"))
            claims = principal_data.get("claims", [])
            
            # Extract roles from the claims
            roles = [
                c.get("val") for c in claims 
                if c.get("typ") in ["roles", "http://schemas.microsoft.com/ws/2008/06/identity/claims/role"]
            ]
            
            if "User" not in roles:
                return False, 403, "Access denied. Required role 'User' is missing."
                
            return True, 200, ""
        except Exception as e:
            return False, 401, f"Failed to parse Easy Auth principal: {str(e)}"
            
    # 2. Local Fallback / Bearer Token Path (Development/Local testing)
    auth_header = req.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return False, 401, "Missing or invalid authorization. Easy Auth principal header or Bearer token expected."
        
    token = auth_header.split(" ")[1]
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return False, 401, "Malformed token structure."
        
        payload_b64 = parts[1]
        payload_b64 += '=' * (4 - len(payload_b64) % 4)  # Add padding if required
        payload_json = base64.urlsafe_b64decode(payload_b64).decode('utf-8')
        payload = json.loads(payload_json)
        
        roles = payload.get("roles", [])
        if isinstance(roles, str):
            roles = [roles]
            
        if "User" not in roles:
            return False, 403, "Access denied. Required role 'User' is missing."
            
        return True, 200, ""
    except Exception as e:
        return False, 401, f"Failed to parse Bearer token: {str(e)}"

@app.route(route="tasks", methods=["GET"])
def get_tasks(req: func.HttpRequest) -> func.HttpResponse:
    """Retrieve all current tasks from Cosmos DB."""
    logging.info("HTTP trigger - GET /api/tasks")
    
    # Authenticate and Authorize
    authorized, status_code, err_msg = is_authorized(req)
    if not authorized:
        return func.HttpResponse(
            body=json.dumps({"error": err_msg}),
            mimetype="application/json",
            status_code=status_code
        )
        
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
    
    # Authenticate and Authorize
    authorized, status_code, err_msg = is_authorized(req)
    if not authorized:
        return func.HttpResponse(
            body=json.dumps({"error": err_msg}),
            mimetype="application/json",
            status_code=status_code
        )
        
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
    
    # Authenticate and Authorize
    authorized, status_code, err_msg = is_authorized(req)
    if not authorized:
        return func.HttpResponse(
            body=json.dumps({"error": err_msg}),
            mimetype="application/json",
            status_code=status_code
        )
        
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
    
    # Authenticate and Authorize
    authorized, status_code, err_msg = is_authorized(req)
    if not authorized:
        return func.HttpResponse(
            body=json.dumps({"error": err_msg}),
            mimetype="application/json",
            status_code=status_code
        )
        
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

# to deploy func azure functionapp publish vovy-rest-api