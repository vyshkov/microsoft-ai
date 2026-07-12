import os
import sys
import json
import requests

# Add the current directory to sys.path to ensure we can import local modules (auth_helper)
# regardless of the terminal's working directory.
sys.path.append(os.path.dirname(__file__))

from auth_helper import get_user_tokens_via_msal

# Configuration
CLIENT_ID = os.environ.get("AZURE_CLIENT_ID", "d66fe946-550a-4048-9582-432a5ae95561")
TENANT_ID = os.environ.get("AZURE_TENANT_ID", "060e0979-b29c-46cc-9075-0c0478bffd3e")
FUNCTION_URL = os.environ.get("FUNCTION_URL", "https://vovy-rest-api-bxchc2abe3htegc6.eastus-01.azurewebsites.net/api/tasks")

def main():
    print("=== Querying Azure Function Tasks API with authentication ===")
    
    try:
        # 1. Trigger authentication via auth_helper to get the ID Token containing user roles
        auth_data = get_user_tokens_via_msal(CLIENT_ID, TENANT_ID, "access_as_user")
        
        # 2. Extract the ID Token (contains user claims and app roles)
        id_token = auth_data.get("id_token")
        if not id_token:
            print("Error: No ID Token retrieved. Make sure 'openid' and 'profile' scopes are supported.")
            sys.exit(1)
            
        print(f"\nSending authenticated GET request to: {FUNCTION_URL}")
        
        # 3. Setup Authorization header with the ID Token
        headers = {
            "Authorization": f"Bearer {id_token}",
            "Accept": "application/json"
        }
        
        # 4. Perform the HTTP request
        response = requests.get(FUNCTION_URL, headers=headers)
        
        print("\n" + "="*50)
        print(f"API Response: {response.status_code} ({response.reason})")
        print("="*50)
        
        try:
            # Print formatted JSON if successful
            data = response.json()
            print("\nResponse Data:")
            print(json.dumps(data, indent=2))
        except ValueError:
            # Print raw text if not JSON (e.g. error messages)
            print(f"\nRaw Response Body:\n{response.text}")
        print("="*50)
        
    except Exception as e:
        print(f"\nAn error occurred while calling the API: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
