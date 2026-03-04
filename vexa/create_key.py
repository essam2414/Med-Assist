import httpx
import sys

def create_user_and_token():
    admin_url = "http://localhost:8056/admin"
    headers = {"X-Admin-API-Key": "dev-key", "Content-Type": "application/json"}
    
    # 1. Create User
    user_payload = {
        "email": "med-assistant@example.com",
        "name": "Med Assistant System",
        "max_concurrent_bots": 10
    }
    r = httpx.post(f"{admin_url}/users", json=user_payload, headers=headers)
    if r.status_code >= 400:
        # If user exists, we might need to get them
        r = httpx.get(f"{admin_url}/users/email/med-assistant@example.com", headers=headers)
        if r.status_code >= 400:
            print("Failed to ensure user:", r.text)
            sys.exit(1)
            
    user_id = r.json()["id"]
    
    # 2. Create Token
    r_token = httpx.post(f"{admin_url}/users/{user_id}/tokens", headers=headers)
    if r_token.status_code >= 400:
        print("Failed to create token:", r_token.text)
        sys.exit(1)
        
    token = r_token.json()["token"]
    print(f"VEXA_TOKEN={token}")

if __name__ == "__main__":
    create_user_and_token()
