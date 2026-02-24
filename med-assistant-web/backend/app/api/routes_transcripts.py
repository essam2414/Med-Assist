from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.deps import get_db, get_current_user
from app.models.transcript import TranscriptEntry as TranscriptModel
from app.models.consultation import Consultation as ConsultationModel
from app.schemas.transcript import TranscriptEntry, TranscriptEntryCreate
from app.models.user import User

router = APIRouter(prefix="/transcripts", tags=["transcripts"])

@router.post("/", response_model=TranscriptEntry)
def create_transcript(
    payload: TranscriptEntryCreate,
    consultation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify the consultation belongs to the user
    consultation = db.query(ConsultationModel).filter(
        ConsultationModel.id == consultation_id,
        ConsultationModel.doctor_id == current_user.id
    ).first()
    
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")
        
    t = TranscriptModel(
        consultation_id=consultation.id,
        speaker=payload.speaker,
        start_time=payload.start_time,
        end_time=payload.end_time,
        text=payload.text,
        created_at=datetime.utcnow(),
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t

@router.get("/", response_model=List[TranscriptEntry])
def list_transcripts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Get all transcripts for consultations owned by current user
    qs = (
        db.query(TranscriptModel)
        .join(ConsultationModel)
        .filter(ConsultationModel.doctor_id == current_user.id)
        .order_by(TranscriptModel.created_at.desc())
    )
    return list(qs)

@router.get("/{id}", response_model=TranscriptEntry)
def get_transcript(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    t = (
        db.query(TranscriptModel)
        .join(ConsultationModel)
        .filter(
            TranscriptModel.id == id,
            ConsultationModel.doctor_id == current_user.id
        )
        .first()
    )
    if not t:
        raise HTTPException(status_code=404, detail="Transcript not found")
    return t

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transcript(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    t = (
        db.query(TranscriptModel)
        .join(ConsultationModel)
        .filter(
            TranscriptModel.id == id,
            ConsultationModel.doctor_id == current_user.id
        )
        .first()
    )
    if not t:
        raise HTTPException(status_code=404, detail="Transcript not found")
        
    db.delete(t)
    db.commit()
    return None
