import time
import os
import httpx
from fastapi import FastAPI, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient

app = FastAPI()

# Vault Configuration 
VAULT_ROLE_ID = os.getenv("ROLE_ID")
VAULT_SECRET_ID = os.getenv("SECRET_ID")
VAULT_ADDR = os.getenv("VAULT_ADDR")
VAULT_SECRET_PATH = "v1/database/creds/myapp"

# In-memory authentication token cache
vault_token_cache = {"token": None, "expires_at": 0}

async def get_vault_token() -> str:
    """Authenticates with Vault using AppRole and caches the temporary client token."""
    current_time = time.time()
    if vault_token_cache["token"] and vault_token_cache["expires_at"] > current_time + 60:
        return vault_token_cache["token"]
        
    async with httpx.AsyncClient() as client:
        payload = {"role_id": VAULT_ROLE_ID, "secret_id": VAULT_SECRET_ID}
        response = await client.post(f"{VAULT_ADDR}/v1/auth/approle/login", json=payload)
        
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Vault AppRole authentication failed")
            
        auth_data = response.json()["auth"]
        vault_token_cache["token"] = auth_data["client_token"]
        vault_token_cache["expires_at"] = current_time + auth_data["lease_duration"]
        return vault_token_cache["token"]

async def get_db_credentials(token: str = Depends(get_vault_token)) -> dict:
    """Uses the temporary token to request active dynamic database credentials."""
    headers = {"X-Vault-Token": token}
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{VAULT_ADDR}/{VAULT_SECRET_PATH}", headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to get dynamic DB credentials from Vault")
        return response.json()["data"]

async def get_mongo_client(creds: dict = Depends(get_db_credentials)) -> AsyncIOMotorClient:
    """Builds a MongoDB client pool utilizing the dynamically rotated credentials."""
    username = creds["username"]
    password = creds["password"]
    connection_string = f"mongodb://{username}:{password}@mongodb.host:27017/my_database"
    return AsyncIOMotorClient(connection_string)

@app.get("/school-info")
async def show_school_info(client: AsyncIOMotorClient = Depends(get_mongo_client)):
    """Fetches the Liora document and displays it on the screen."""
    db = client.get_database("my_database")
    
    # Query MongoDB for the newly inserted record
    school_record = await db.schools.find_one({"name": "Liora", "product": "devops"})
    
    if not school_record:
        raise HTTPException(status_code=404, detail="School data not found in database")
    
    # Convert MongoDB _id Object to string for JSON serialization
    school_record["_id"] = str(school_record["_id"])
    
    # Print the specific target information directly to server logs
    print(f"\n--- SCREEN OUTPUT: {school_record['name']} | {school_record['product']} ---")
    print(f"Address: {school_record['location']['address']}\n")
    
    return {
        "status": "success",
        "data": school_record
    }

