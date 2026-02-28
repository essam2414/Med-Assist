import requests
import json

# Replace with a valid consultation ID from your database
CONSULTATION_ID = 1 
MEETING_URL = "https://meet.google.com/abc-defg-hij" # Example URL

# If you have a session cookie, you'll need to provide it
# For now, let's just see if we can reach the endpoint
def test_join():
    url = f"http://localhost:8000/recall/join?consultation_id={CONSULTATION_ID}"
    payload = {"meeting_url": MEETING_URL}
    
    try:
        # Note: This will likely fail with 401 if authentication is required
        # but it helps verify if the route is registered and responding
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_join()
