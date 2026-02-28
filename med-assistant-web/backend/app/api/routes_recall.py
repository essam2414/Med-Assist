from fastapi import APIRouter, Depends, HTTPException, Request, Body
from sqlalchemy.orm import Session
from app.deps import get_db, get_current_user
from app.models.consultation import Consultation as ConsultationModel
from app.models.transcript import TranscriptEntry as TranscriptModel
from app.models.user import User
from app.services.recall_service import recall_service
from app.core.config import settings
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/recall", tags=["recall"])

@router.post("/join")
async def join_meeting(
    consultation_id: int,
    meeting_url: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify consultation belongs to user
    consultation = db.query(ConsultationModel).filter(
        ConsultationModel.id == consultation_id,
        ConsultationModel.doctor_id == current_user.id
    ).first()

    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")

    # Hardcoded base webhook for simplicity in this dev environment
    # In prod, this would be a config or dynamic
    webhook_base = "https://lazy-bears-train.loca.lt"
    webhook_url = f"{webhook_base}/recall/webhook"

    try:
        bot_data = await recall_service.create_bot(
            meeting_url=meeting_url,
            bot_name=f"MedAssist - {current_user.name}",
            webhook_url=webhook_url
        )
        
        bot_id = bot_data.get("id")
        print(f"DEBUG: join_meeting received bot_id: {bot_id}")
        consultation.recall_bot_id = bot_id
        db.commit()
        print(f"DEBUG: Saved bot_id {bot_id} to consultation {consultation.id}")
        
        return {"status": "success", "bot_id": bot_id}
    except Exception as e:
        logger.error(f"Detailed failure joining meeting: {str(e)}")
        # Pass the inner exception message to the client
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/webhook")
async def test_webhook():
    return {"status": "ok", "message": "Webhook endpoint is reachable"}

@router.post("/webhook")
async def recall_webhook(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
        # Using print for guaranteed visibility in user terminal
        print(f"DEBUG: Recall Webhook Event: {data.get('event')}")
        print(f"DEBUG: Payload Keys: {list(data.keys())}")
        if "data" in data:
             print(f"DEBUG: Data Keys: {list(data['data'].keys())}")
    except Exception:
        logger.error("Failed to parse Recall webhook JSON")
        return {"status": "error"}

    event_type = data.get("event")
    
    # Try multiple locations for bot_id based on Recall v1 logs
    bot_id = data.get("bot_id")
    if not bot_id and "data" in data:
        # Check data -> bot -> id
        bot_id = data["data"].get("bot", {}).get("id")
    if not bot_id and "data" in data:
        # Check data -> data -> bot -> id (double nested)
        inner_data = data["data"]
        if isinstance(inner_data, dict):
            bot_id = inner_data.get("bot", {}).get("id") or inner_data.get("bot_id")
        
    if not bot_id:
        print(f"WARNING: Webhook received without bot_id. Payload keys: {list(data.keys())}")
        return {"status": "ignored"}

    if event_type == "transcript.data":
        inner_data = data.get("data", {})
        # Logs show: data -> data -> words []
        transcript_info = inner_data.get("data", {})
        words = transcript_info.get("words", [])
        speaker = transcript_info.get("participant", {}).get("name", "Bot/Participant")
        
        # Reconstruct text from words array
        text = " ".join([w.get("text", "") for w in words]).strip()
        
        # Extract timestamps from words
        start_time = 0.0
        end_time = 0.0
        if words:
            start_time = words[0].get("start_timestamp", {}).get("relative", 0.0)
            end_time = words[-1].get("end_timestamp", {}).get("relative", 0.0)

        if not text and "transcript" in inner_data:
            # Fallback for other versions
            text = inner_data.get("transcript", {}).get("text", "")
            start_time = inner_data.get("transcript", {}).get("start_time", 0.0)
            end_time = inner_data.get("transcript", {}).get("end_time", 0.0)

        if text:
            # Find the consultation associated with this bot
            consultation = db.query(ConsultationModel).filter(ConsultationModel.recall_bot_id == bot_id).first()
            if not consultation:
                print(f"DEBUG: No consultation found for bot_id {bot_id} in DB")
                return {"status": "ignored"}

            new_entry = TranscriptModel(
                consultation_id=consultation.id,
                speaker=speaker,
                text=text,
                start_time=start_time,
                end_time=end_time,
                created_at=datetime.utcnow()
            )
            db.add(new_entry)
            db.commit()
            print(f"DEBUG: Saved transcript to consultation {consultation.id}: [{speaker}] {text[:50]}...")

    elif event_type in ["bot.status_change", "bot_status_change", "bot.call_ended", "bot.done"]:
        # Lifecycle events
        status_data = data.get("data", {})
        status = status_data.get("status") or data.get("status")
        logger.info(f"Bot {bot_id} status change: {status}")
        
        # If call ended, clear the bot id so UI updates
        if status in ["call_ended", "done", "fatal", "leaving_call"]:
            consultation = db.query(ConsultationModel).filter(ConsultationModel.recall_bot_id == bot_id).first()
            if consultation:
                consultation.recall_bot_id = None
                db.commit()
                logger.info(f"Cleared recall_bot_id for consultation {consultation.id} as bot left")

    return {"status": "received"}

@router.post("/disconnect")
async def disconnect_bot(
    consultation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    consultation = db.query(ConsultationModel).filter(
        ConsultationModel.id == consultation_id,
        ConsultationModel.doctor_id == current_user.id
    ).first()

    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")

    if consultation.recall_bot_id:
        await recall_service.leave_call(consultation.recall_bot_id)

    consultation.recall_bot_id = None
    db.commit()
    return {"status": "success"}
