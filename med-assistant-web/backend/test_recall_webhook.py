import requests
import json
import uuid

# Configuration
API_URL = "http://localhost:8000/recall/webhook"
BOT_ID = str(uuid.uuid4())
CONSULTATION_ID = 1 # Change this to an existing consultation ID if needed

def simulate_webhook(bot_id, text, speaker="Patient"):
    payload = {
        "event": "bot.transcript",
        "data": {
            "bot_id": bot_id,
            "transcript": {
                "text": text,
                "speaker": speaker,
                "language": "en-US"
            }
        }
    }
    
    print(f"Sending mock transcript: '{text}' for bot {bot_id}")
    try:
        response = requests.post(API_URL, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Note: You need to have a consultation with this recall_bot_id in the DB
    # or the webhook will return {"status": "ignored"}
    print("This script simulates a Recall.ai webhook.")
    print("Example usage: Run this after inviting a bot and noting the bot_id.")
    
    # Example call (will likely be ignored unless BOT_ID matches a row in DB)
    simulate_webhook(BOT_ID, "Hello, this is a live transcript from the Recall bot.")
