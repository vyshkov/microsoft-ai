import os
import sys
import json
from datetime import datetime, timezone
import msal

def get_user_tokens_via_msal(client_id: str, tenant_id: str, scope_name: str = ".default") -> dict:
    """
    Acquires tokens (both Access Token and ID Token) using MSAL directly.
    MSAL's acquire_token_interactive launches the browser and returns the full response dictionary.
    
    :param client_id: The Client ID of your App Registration.
    :param tenant_id: Your Directory (tenant) ID.
    :param scope_name: The scope name (e.g., '.default').
    :return: A dictionary containing 'access_token', 'id_token', 'id_claims', and 'expires_at'.
    """
    # 1. Initialize MSAL PublicClientApplication
    authority = f"https://login.microsoftonline.com/{tenant_id}"
    app = msal.PublicClientApplication(
        client_id=client_id,
        authority=authority
    )
    
    # 2. Fully qualify the scope and add OIDC scopes (openid, profile) to ensure we get an ID token
    if scope_name == ".default":
        api_scope = f"api://{client_id}/.default"
    elif scope_name.startswith("api://"):
        api_scope = scope_name
    else:
        api_scope = f"api://{client_id}/{scope_name}"
        
    scopes = [api_scope]
    
    print(f"Initializing authentication for client: {client_id}")
    print(f"Authority: {authority}")
    print(f"Requesting scopes: {scopes}")
    
    # 3. Interactive login
    result = app.acquire_token_interactive(scopes=scopes)
    
    if "error" in result:
        raise Exception(f"MSAL Error: {result.get('error_description', result.get('error'))}")
        
    # Convert expiration timestamp
    expires_on = result.get("expires_in", 3600) + int(datetime.now().timestamp())
    expires_dt = datetime.fromtimestamp(expires_on, tz=timezone.utc)
    
    return {
        "access_token": result.get("access_token"),
        "id_token": result.get("id_token"),
        "id_claims": result.get("id_token_claims", {}),
        "expires_at": expires_dt
    }

if __name__ == "__main__":
    print("=== Entra ID Interactive Authentication POC (MSAL Direct) ===\n")
    
    # Configure variables
    client_id = os.environ.get("AZURE_CLIENT_ID", "d66fe946-550a-4048-9582-432a5ae95561")
    tenant_id = os.environ.get("AZURE_TENANT_ID", "060e0979-b29c-46cc-9075-0c0478bffd3e")
            
    try:
        # Request tokens using MSAL
        auth_data = get_user_tokens_via_msal(client_id, tenant_id, "access_as_user")
        
        print("\n" + "="*50)
        print(" AUTHENTICATION SUCCESSFUL")
        print("="*50)
        
        print(f"\nAccess Token:\n{auth_data['access_token']}")
        
        print("\n" + "-"*50)
        print(f"ID Token (For user identification):\n{auth_data['id_token']}")
        print(f"\nID Token Decoded Claims:")
        print(json.dumps(auth_data['id_claims'], indent=2))
        print("-"*50)
        
        print(f"\nExpires On (UTC): {auth_data['expires_at'].strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"Expires On (Local): {auth_data['expires_at'].astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print("="*50)
        
    except Exception as e:
        print(f"\nFailed to acquire token: {e}", file=sys.stderr)
