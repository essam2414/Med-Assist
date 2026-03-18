from fastapi import APIRouter, Depends, HTTPException, Request, Body, BackgroundTasks
from sqlalchemy.orm import Session
from app.deps import get_db, get_current_user
from app.models.consultation import Consultation as ConsultationModel
from app.models.transcript import TranscriptEntry as TranscriptModel
from app.models.user import User
from app.services.vexa_service import vexa_service
from app.core.config import settings
from app.services.live_insight_service import evaluate_and_generate_live_insights
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

    try:
        # We still use the /recall/join route for frontend compatibility
        native_meeting_id = await vexa_service.create_bot(
            meeting_url=meeting_url,
            bot_name=f"MedAssist - {current_user.name}"
        )
        
        print(f"DEBUG: join_meeting mapped to native_meeting_id: {native_meeting_id}")
        consultation.recall_bot_id = native_meeting_id # reuse column
        db.commit()
        print(f"DEBUG: Saved native_meeting_id {native_meeting_id} to consultation {consultation.id}")
        
        return {"status": "success", "bot_id": native_meeting_id}
    except Exception as e:
        logger.error(f"Detailed failure joining meeting: {str(e)}")
        # Pass the inner exception message to the client
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/webhook")
async def test_webhook():
    return {"status": "ok", "message": "Webhook endpoint is reachable"}

@router.post("/webhook")
async def recall_webhook(request: Request, db: Session = Depends(get_db)):
    # With Vexa, we do not need the webhook for transcripts because we are pulling.
    # We can handle lifecycle events here if Vexa is configured to send webhooks.
    try:
        data = await request.json()
        print(f"DEBUG: Webhook Event payload keys: {list(data.keys())}")
        
        event_type = data.get("event_type")
        if event_type == "meeting.status_change":
            meeting = data.get("meeting", {})
            status = meeting.get("status")
            native_id = meeting.get("native_meeting_id")
            
            logger.info(f"Vexa bot {native_id} status change: {status}")
            if status in ["completed", "failed"]:
                consultation = db.query(ConsultationModel).filter(ConsultationModel.recall_bot_id == native_id).first()
                if consultation:
                    consultation.recall_bot_id = None
                    db.commit()
                    logger.info(f"Cleared bot_id for consultation {consultation.id} as meeting ended")

    except Exception:
        logger.error("Failed to parse webhook JSON")
        return {"status": "error"}

    return {"status": "received"}

@router.post("/disconnect")
async def disconnect_bot(
    consultation_id: int,
    background_tasks: BackgroundTasks,
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
        # Final sync before bot leaves
        await vexa_service.sync_transcripts(consultation, db)
        background_tasks.add_task(evaluate_and_generate_live_insights, consultation.id)
        await vexa_service.leave_call(consultation.recall_bot_id)

    consultation.recall_bot_id = None
    db.commit()
    return {"status": "success"}
