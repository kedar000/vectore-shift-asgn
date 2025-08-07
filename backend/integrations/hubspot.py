# slack.py
import json
import secrets
from redis_client import add_key_value_redis
from fastapi import Request
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
import httpx
import urllib.parse


from redis_client import get_value_redis, delete_key_redis, add_key_value_redis

CLIENT_ID = 'c02368b9-0015-408e-a382-cad754293da4'  
CLIENT_SECRET = 'dd39b552-2e6c-4c2f-9c3f-74d7a350c595'  #because its an assignment i just hardcoded the cliendId and secret
REDIRECT_URI = 'http://localhost:8000/integrations/hubspot/oauth2callback'
# SCOPES = "oauth crm.objects.contacts.read"  # 'oauth' MUST come first
SCOPES = "oauth crm.objects.companies.read crm.objects.contacts.read"  # 'oauth' MUST come first
ENCODED_SCOPES = urllib.parse.quote(SCOPES)
ENCODED_REDIRECT_URI = urllib.parse.quote(REDIRECT_URI, safe='')


AUTH_URL = 'https://app.hubspot.com/oauth/authorize'

async def authorize_hubspot(user_id, org_id):
    # 1. Generate a safe, short state token
    state_token = secrets.token_urlsafe(32)

    # 2. Store mapping in Redis
    state_data = {
        'user_id': user_id,
        'org_id': org_id
    }
    await add_key_value_redis(f"hubspot_state:{state_token}", json.dumps(state_data), expire=600)

    # 3. Build the OAuth URL
    url = (
        f"{AUTH_URL}"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
        # f"&scope=oauth crm.objects.companies.read crm.objects.contacts.read"
        f"&scope={SCOPES}"
        f"&state={state_token}"
    )

    # 4. Return the URL to the frontend
    return url

async def oauth2callback_hubspot(request: Request):
    # 1. Handle any error returned by HubSpot
    if request.query_params.get('error'):
        raise HTTPException(status_code=400, detail=request.query_params.get('error'))

    # 2. Extract code and state from query params
    code = request.query_params.get('code')
    state_token = request.query_params.get('state')

    # 3. Retrieve the original state data
    saved_state_json = await get_value_redis(f'hubspot_state:{state_token}')
    if not saved_state_json:
        raise HTTPException(status_code=400, detail="Invalid or expired state")

    state_data = json.loads(saved_state_json)
    user_id = state_data.get('user_id')
    org_id = state_data.get('org_id')

    # 4. Exchange the code for access and refresh tokens
    token_url = 'https://api.hubapi.com/oauth/v1/token'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'grant_type': 'authorization_code',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'redirect_uri': REDIRECT_URI,
        'code': code
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=data, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to get tokens from HubSpot")

    token_data = response.json()

    # 5. Save credentials in Redis
    await add_key_value_redis(f'hubspot_credentials:{org_id}:{user_id}', json.dumps(token_data), expire=600)

    # 6. Cleanup
    await delete_key_redis(f'hubspot_state:{state_token}')

    # 7. Return a simple HTML page to close the window
    close_window_script = """
    <html>
        <script>
            window.close();
        </script>
    </html>
    """
    return HTMLResponse(content=close_window_script)

# async def get_hubspot_credentials(user_id, org_id):
#     # TODO
#     pass
async def get_hubspot_credentials(user_id, org_id):
    redis_key = f"hubspot_credentials:{org_id}:{user_id}"
    creds_json = await get_value_redis(redis_key)
    
    if not creds_json:
        raise HTTPException(status_code=404, detail="Credentials not found")
    
    return json.loads(creds_json)

# async def create_integration_item_metadata_object(response_json):
#     # TODO
#     pass

async def create_integration_item_metadata_object(response_json):
    items = []

    for item in response_json.get("results", []):
        properties = item.get("properties", {})
        metadata = {
            "id": item.get("id"),
            "name": f"{properties.get('firstname', '')} {properties.get('lastname', '')}".strip(),
            "email": properties.get("email"),
            "raw_data": item  # Optional: helpful for debugging or deeper inspection
        }
        items.append(metadata)

    return items

# async def get_items_hubspot(credentials):
#     # TODO
#     pass

import httpx

async def get_items_hubspot(credentials):
    access_token = credentials.get("access_token")
    if not access_token:
        raise ValueError("Missing access token in credentials")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    url = "https://api.hubapi.com/crm/v3/objects/contacts?limit=10"

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch items: {response.text}")

        response_json = response.json()

    # Transform response using the helper function
    return await create_integration_item_metadata_object(response_json)