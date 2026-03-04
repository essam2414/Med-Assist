import httpx
from app.core.config import settings
from app.models.transcript import TranscriptEntry
from datetime import datetime
import logging
import re
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class VexaService:
    def __init__(self):
        # Local Vexa instances
        self.gateway_base_url = "http://localhost:8056"
        self.collector_base_url = "http://localhost:8123"

    @property
    def headers(self):
        # Define API Key header. If no API key is enforced locally, this can be empty or a dummy value
        return {
            "Content-Type": "application/json",
            "X-API-Key": "jb6gLEGcJabjOf7LWACNDFigWV7BxAcwEj4GCjKH" # Generated API token for Med-Assistant user
        }

    def _extract_google_meet_id(self, url: str) -> str:
        """Extracts the native meeting ID (e.g., abc-defg-hij) from a Google Meet URL."""
        # Check if the format is like meet.google.com/abc-defg-hij
        match = re.search(r'meet\.google\.com/([a-z0-9-]+)', url)
        if match:
            return match.group(1)
        raise ValueError("Invalid Google Meet URL provided. Could not extract meeting ID.")

    async def create_bot(self, meeting_url: str, bot_name: str):
        """
        Creates a Vexa bot to join a Google Meet meeting.
        """
        native_meeting_id = self._extract_google_meet_id(meeting_url)
        
        payload = {
            "platform": "google_meet",
            "native_meeting_id": native_meeting_id,
            "bot_name": bot_name,
            "voice_agent_enabled": False, # Just listening for consultation
            "transcribe_enabled": True
        }
        
        async with httpx.AsyncClient() as client:
            try:
                logger.info(f"Creating Vexa bot for Google Meet ID {native_meeting_id}")
                response = await client.post(
                    f"{self.gateway_base_url}/bots",
                    json=payload,
                    headers=self.headers,
                    timeout=30.0
                )
                logger.info(f"Vexa API response status: {response.status_code}")
                if response.status_code >= 400:
                    logger.error(f"Vexa API error body: {response.text}")
                
                response.raise_for_status()
                # Return the native_meeting_id so it can be stored instead of a recall_bot_id
                return native_meeting_id
            except httpx.HTTPStatusError as e:
                error_detail = e.response.text
                logger.error(f"Vexa API HTTP error: {error_detail}")
                raise Exception(f"Vexa API error ({e.response.status_code}): {error_detail}")
            except Exception as e:
                logger.error(f"Unexpected error creating Vexa bot: {str(e)}")
                raise e

    async def leave_call(self, native_meeting_id: str):
        """
        Tells the Vexa bot to leave the Google Meet call.
        """
        async with httpx.AsyncClient() as client:
            try:
                logger.info(f"Telling Vexa bot to leave native meeting {native_meeting_id}")
                response = await client.delete(
                    f"{self.gateway_base_url}/bots/google_meet/{native_meeting_id}",
                    headers=self.headers,
                    timeout=30.0
                )
                logger.info(f"Vexa leave response status: {response.status_code}")
                response.raise_for_status()
                return True
            except Exception as e:
                logger.error(f"Error telling Vexa bot to leave: {str(e)}")
                return False

    async def sync_transcripts(self, consultation, db):
        """
        Fetches the latest transcript segments from Vexa and updates the database.
        Replaces all existing transcripts for the consultation with the freshest list.
        """
        if not consultation.recall_bot_id:
            return

        native_meeting_id = consultation.recall_bot_id # We stored it here
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.collector_base_url}/transcripts/google_meet/{native_meeting_id}",
                    headers=self.headers,
                    timeout=15.0
                )
                if response.status_code == 404:
                    return # No transcript yet
                response.raise_for_status()
                
                data = response.json()
                segments = data.get("segments", [])
                
                if segments:
                    # Clear out the existing transcripts for this exact consultation and insert fresh ones
                    # That allows real-time segments (which can change) to be properly represented.
                    db.query(TranscriptEntry).filter(TranscriptEntry.consultation_id == consultation.id).delete()
                    
                    for seg in segments:
                        text = seg.get("text", "").strip()
                        speaker = seg.get("speaker", "Unknown")
                        start_time = seg.get("start", 0.0)
                        end_time = seg.get("end", 0.0)
                        
                        if text:
                            new_entry = TranscriptEntry(
                                consultation_id=consultation.id,
                                speaker=speaker,
                                text=text,
                                start_time=start_time,
                                end_time=end_time,
                                created_at=datetime.utcnow()
                            )
                            db.add(new_entry)
                    db.commit()
            except Exception as e:
                logger.error(f"Error syncing transcripts from Vexa: {str(e)}")

vexa_service = VexaService()
