import os
import sys
from datetime import datetime, timezone
from azure.identity import InteractiveBrowserCredential

def get_user_token(client_id: str, tenant_id: str = None, scope_name: str = ".default") -> tuple[str, datetime]:
    """
    Acquires an Entra ID access token interactively by launching the system browser.
    
    :param client_id: The Client ID of your App Registration.
    :param tenant_id: Your Directory (tenant) ID. Explicitly specifying this prevents multi-tenant login loops.
    :param scope_name: The scope/permission name defined on the API. Defaults to '.default'.
    :return: A tuple of (access_token_string, expiration_datetime_object)
    """
    # 1. Fully qualify the scope.
    if scope_name == ".default":
        scope = f"api://{client_id}/.default"
    elif scope_name.startswith("api://"):
        scope = scope_name
    else:
        scope = f"api://{client_id}/{scope_name}"
        
    print(f"Initializing authentication for client: {client_id}")
    print(f"Tenant ID: {tenant_id or 'Common (Multi-tenant)'}")
    print(f"Requesting scope: {scope}")
    
    # 2. Initialize the credential with Client ID and Tenant ID.
    # Specifying tenant_id forces MSAL to route directly to your directory rather than prompt-looping.
    credential = InteractiveBrowserCredential(
        client_id=client_id,
        tenant_id=tenant_id
    )
    
    # 3. Request the token
    token_info = credential.get_token(scope)
    
    # Convert expiration timestamp
    expires_dt = datetime.fromtimestamp(token_info.expires_on, tz=timezone.utc)
    
    return token_info.token, expires_dt

if __name__ == "__main__":
    print("=== Entra ID Interactive Authentication POC ===\n")
    
    # Configure variables (retrieved from environment or defaults)
    client_id = os.environ.get("AZURE_CLIENT_ID", "d66fe946-550a-4048-9582-432a5ae95561")
    tenant_id = os.environ.get("AZURE_TENANT_ID", "060e0979-b29c-46cc-9075-0c0478bffd3e")
            
    try:
        # Request the default scope
        token, expires_at = get_user_token(client_id, tenant_id, "access_as_user")
        
        print("\n" + "="*50)
        print(" AUTHENTICATION SUCCESSFUL")
        print("="*50)
        print(f"\nAccess Token:\n{token}")
        print("\n" + "="*50)
        print(f"Expires On (UTC): {expires_at.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"Expires On (Local): {expires_at.astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print("="*50)
        
    except Exception as e:
        print(f"\nFailed to acquire token: {e}", file=sys.stderr)
