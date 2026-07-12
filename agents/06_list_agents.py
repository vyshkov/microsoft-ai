import os
import sys
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

# Reconfigure stdout to use UTF-8 on Windows console to prevent encoding crashes
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# Load environment variables if a .env file exists
load_dotenv()

# Configuration
endpoint = os.environ.get("PROJECT_ENDPOINT", "https://vovyaz-test-foundry-1.services.ai.azure.com/api/projects/proj-default")

print(f"Initializing AIProjectClient with endpoint: {endpoint}...")
project_client = AIProjectClient(
    endpoint=endpoint,
    credential=DefaultAzureCredential(),
)

print("Fetching agents from Azure AI project...")
try:
    agents = project_client.agents.list()
    
    # Materialize the iterator
    agent_list = list(agents)
    if not agent_list:
        print("No agents found in this Azure AI project.")
    else:
        print(f"\nFound {len(agent_list)} agent(s):\n")
        print(f"{'Name':<35} | {'ID':<36}")
        print("-" * 75)
        for agent in agent_list:
            agent_name = getattr(agent, "name", "N/A")
            agent_id = getattr(agent, "id", "N/A")
            print(f"{agent_name:<35} | {agent_id:<36}")
            
            # Print additional details if available (e.g. model, instructions, description)
            details = []
            for attr in ["model", "instructions", "description"]:
                if hasattr(agent, attr) and getattr(agent, attr):
                    val = getattr(agent, attr)
                    if attr == "instructions" and len(val) > 80:
                        val = val[:77] + "..."
                    details.append(f"  {attr.capitalize()}: {val}")
            
            if details:
                for detail in details:
                    print(detail)
                print()  # Empty line separator
except Exception as e:
    print(f"Error listing agents: {e}")
