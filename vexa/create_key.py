import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def request_json(url, method, headers, payload=None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Vexa API returned HTTP {error.code}: {detail}") from error

def create_user_and_token():
    admin_token = os.getenv("ADMIN_API_TOKEN")
    if not admin_token:
        env_file = Path(__file__).with_name(".env")
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if line.strip().startswith("ADMIN_API_TOKEN="):
                    admin_token = line.split("=", 1)[1].strip().strip("\"'")
                    break
    if not admin_token:
        print("Set ADMIN_API_TOKEN to the value from vexa/.env before running this script.")
        sys.exit(1)
    admin_url = "http://localhost:8056/admin"
    headers = {"X-Admin-API-Key": admin_token, "Content-Type": "application/json"}
    
    # 1. Create User
    user_payload = {
        "email": "med-assistant@example.com",
        "name": "Med Assistant System",
        "max_concurrent_bots": 10
    }
    try:
        user = request_json(f"{admin_url}/users", "POST", headers, user_payload)
    except RuntimeError:
        # Reuse the existing integration user if it was already created.
        try:
            user = request_json(
                f"{admin_url}/users/email/med-assistant@example.com", "GET", headers
            )
        except RuntimeError as error:
            print("Failed to ensure Vexa user:", error)
            sys.exit(1)

    user_id = user["id"]
    
    # 2. Create Token
    try:
        token_data = request_json(
            f"{admin_url}/users/{user_id}/tokens", "POST", headers
        )
    except RuntimeError as error:
        print("Failed to create token:", error)
        sys.exit(1)
        
    token = token_data["token"]
    print(f"VEXA_TOKEN={token}")

if __name__ == "__main__":
    create_user_and_token()
