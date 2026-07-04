import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

# Load environment variables from .env file if present
load_dotenv()

def main():
    print("==================================================")
    print("   Azure AI Foundry SDK - Hello World / Test      ")
    print("==================================================")
    
    # 1. Verify library imports
    print("[OK] Successfully imported azure.identity")
    print("[OK] Successfully imported azure.ai.projects")
    
    # 2. Check for environment variables
    # Typically needed for Azure AI Projects:
    # PROJECT_CONNECTION_STRING - The connection string for the Azure AI Foundry Project
    connection_string = os.getenv("PROJECT_CONNECTION_STRING")
    
    if connection_string:
        print(f"[INFO] Found PROJECT_CONNECTION_STRING: {connection_string[:30]}...")
        try:
            print("[INFO] Initializing AIProjectClient...")
            # Initialize the client using DefaultAzureCredential (supports Azure CLI, VS Code, env vars, etc.)
            client = AIProjectClient.from_connection_string(
                credential=DefaultAzureCredential(),
                conn_str=connection_string
            )
            print("[OK] Successfully initialized AIProjectClient!")
            print(f"[INFO] Project location: {client.scope.location}")
            
        except Exception as e:
            print(f"[ERROR] Failed to initialize AIProjectClient: {e}")
            print("[INFO] Note: To connect to Azure AI Foundry, run 'az login' first or set up credentials.")
    else:
        print("[WARN] PROJECT_CONNECTION_STRING not found in environment or .env file.")
        print("[INFO] To use the SDK with your Azure AI Foundry project:")
        print("    1. Create a '.env' file in this directory.")
        print("    2. Add: PROJECT_CONNECTION_STRING=\"<your-project-connection-string>\"")
        print("    3. Run 'az login' in your terminal to authenticate.")

    print("\nHello World! MS Foundry AI project initialized successfully.")

if __name__ == "__main__":
    main()
