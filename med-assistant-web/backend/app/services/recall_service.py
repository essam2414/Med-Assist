import httpx
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class RecallService:
    def __init__(self):
        logger.info(f"RecallService initialized with region: {settings.RECALL_REGION}")
        # We'll compute the base URL dynamically in create_bot to ensure we use the latest settings
        pass

    @property
    def base_url(self):
        region = settings.RECALL_REGION
        if region == "us-east-1":
            return "https://api.recall.ai/api/v1"
        return f"https://{region}.recall.ai/api/v1"

    @property
    def headers(self):
        return {
            "Authorization": f"Token {settings.RECALL_API_KEY}",
            "Content-Type": "application/json"
        }

    async def create_bot(self, meeting_url: str, bot_name: str, webhook_url: str):
        """
        Creates a bot to join a meeting.
        """
        payload = {
            "meeting_url": meeting_url,
            "bot_name": bot_name,
            "webhook_url": webhook_url, # For lifecycle events
            "recording_config": {
                "transcript": {
                    "provider": {
                        "assembly_ai_v3_streaming": {},
                    }
                },
                "realtime_endpoints": [
                    {
                        "url": webhook_url,
                        "type": "webhook",
                        "events": ["transcript.data"]
                    }
                ]
            }
        }
        
        async with httpx.AsyncClient() as client:
            try:
                logger.info(f"Creating Recall bot for {meeting_url} with webhook {webhook_url}")
                logger.info(f"Recall API Target URL: {self.base_url}/bot")
                response = await client.post(
                    f"{self.base_url}/bot",
                    json=payload,
                    headers=self.headers,
                    timeout=30.0
                )
                logger.info(f"Recall API response status: {response.status_code}")
                if response.status_code >= 400:
                    logger.error(f"Recall API error body: {response.text}")
                
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                error_detail = e.response.text
                logger.error(f"Recall API HTTP error: {error_detail}")
                raise Exception(f"Recall API error ({e.response.status_code}): {error_detail}")
            except Exception as e:
                logger.error(f"Unexpected error creating Recall bot: {str(e)}")
                raise e

    async def leave_call(self, bot_id: str):
        """
        Tells the bot to leave the call.
        """
        async with httpx.AsyncClient() as client:
            try:
                logger.info(f"Telling Recall bot {bot_id} to leave the call")
                response = await client.post(
                    f"{self.base_url}/bot/{bot_id}/leave_call/",
                    headers=self.headers,
                    timeout=30.0
                )
                logger.info(f"Recall leave response status: {response.status_code}")
                response.raise_for_status()
                return True
            except Exception as e:
                logger.error(f"Error telling bot to leave: {str(e)}")
                # We don't raise here because we still want to clear the DB ID
                return False

recall_service = RecallService()
