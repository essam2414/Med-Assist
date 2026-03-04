from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
from typing import List

from app.deps import get_db, get_current_user
from app.models.consultation import Consultation as ConsultationModel
from app.models.transcript import TranscriptEntry
from app.models.insight import AIInsight
from app.schemas.consultation import Consultation, ConsultationCreate
from app.models.user import User
from app.services.vexa_service import vexa_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/consultations", tags=["consultations"])


@router.post("/", response_model=Consultation)
def create_consultation(
    payload: ConsultationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    c = ConsultationModel(
        title=payload.title,
        doctor_id=current_user.id,
        patient_id=payload.patient_id,
        status="draft",
        created_at=datetime.utcnow(),
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@router.get("/", response_model=List[Consultation])
async def list_consultations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    qs = (
        db.query(ConsultationModel)
        .options(
            joinedload(ConsultationModel.transcripts), 
            joinedload(ConsultationModel.insights),
            joinedload(ConsultationModel.patient)
        )
        .filter(ConsultationModel.doctor_id == current_user.id)
        .order_by(ConsultationModel.created_at.desc())
    )
    consultations = list(qs)
    
    # Sync transcripts for active consultations
    for c in consultations:
        if c.status == "draft" and c.recall_bot_id:
            await vexa_service.sync_transcripts(c, db)
            
    # Refresh the instances heavily joined if any synced
    if any(c.status == "draft" and c.recall_bot_id for c in consultations):
        # easiest just to requery the active ones or the whole list so transcripts are loaded
        qs = (
            db.query(ConsultationModel)
            .options(
                joinedload(ConsultationModel.transcripts), 
                joinedload(ConsultationModel.insights),
                joinedload(ConsultationModel.patient)
            )
            .filter(ConsultationModel.doctor_id == current_user.id)
            .order_by(ConsultationModel.created_at.desc())
        )
        return list(qs)

    return consultations
@router.delete("/{consultation_id}")
def delete_consultation(
    consultation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    c = (
        db.query(ConsultationModel)
        .filter(
            ConsultationModel.id == consultation_id,
            ConsultationModel.doctor_id == current_user.id,
        )
        .first()
    )
    if not c:
        raise HTTPException(status_code=404, detail="Consultation not found")

    db.query(TranscriptEntry).filter(TranscriptEntry.consultation_id == c.id).delete()
    db.query(AIInsight).filter(AIInsight.consultation_id == c.id).delete()
    db.delete(c)
    db.commit()
    return {"status": "ok"}


@router.patch("/{consultation_id}")
async def update_consultation(
    consultation_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    c = (
        db.query(ConsultationModel)
        .filter(
            ConsultationModel.id == consultation_id,
            ConsultationModel.doctor_id == current_user.id,
        )
        .first()
    )
    if not c:
        raise HTTPException(status_code=404, detail="Consultation not found")
    
    if "status" in payload:
        c.status = payload["status"]
        if payload["status"] == "completed":
            c.ended_at = datetime.utcnow()
            if c.recall_bot_id:
                try:
                    await vexa_service.leave_call(c.recall_bot_id)
                except Exception as e:
                    logger.warning(f"Failed to leave call for bot {c.recall_bot_id}: {e}")
                # We optionally clear recall_bot_id to show disconnected, or keep it to link to Vexa
                c.recall_bot_id = None
    
    db.commit()
    db.refresh(c)
    return c


@router.get("/active")
async def get_active_consultation(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    c = (
        db.query(ConsultationModel)
        .options(
            joinedload(ConsultationModel.transcripts), 
            joinedload(ConsultationModel.insights),
            joinedload(ConsultationModel.patient)
        )
        .filter(
            ConsultationModel.doctor_id == current_user.id,
            ConsultationModel.status == "draft" # Or "active"
        )
        .order_by(ConsultationModel.created_at.desc())
        .first()
    )
    if c and c.recall_bot_id:
        await vexa_service.sync_transcripts(c, db)
        db.refresh(c)
    return c
