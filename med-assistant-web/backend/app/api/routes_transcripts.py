import tempfile
import os
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.deps import get_db, get_current_user
from app.models.transcript import TranscriptEntry as TranscriptModel
from app.models.consultation import Consultation as ConsultationModel
from app.schemas.transcript import TranscriptEntry, TranscriptEntryCreate
from app.models.user import User
from app.services.stt_service import transcribe_audio

router = APIRouter(prefix="/transcripts", tags=["transcripts"])

@router.post("/upload", response_model=List[TranscriptEntry])
def upload_and_transcribe(
    audio: UploadFile = File(...),
    consultation_id: int = Form(...),
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
        
    # Save UploadFile to a temporary file
    try:
        suffix = os.path.splitext(audio.filename)[1] if audio.filename else ".webm"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_audio:
            temp_audio.write(audio.file.read())
            temp_path = temp_audio.name
            
        try:
            # Transcribe the audio, getting a list of dict segments
            transcript_segments = transcribe_audio(temp_path)
        finally:
            # Clean up the temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error transcribing audio: {str(e)}")

    # Create the db records
    created_transcripts = []
    for segment in transcript_segments:
        t = TranscriptModel(
            consultation_id=consultation.id,
            speaker=segment["speaker"], 
            start_time=segment["start_time"],
            end_time=segment["end_time"],
            text=segment["text"],
            created_at=datetime.utcnow(),
        )
        db.add(t)
        created_transcripts.append(t)
        
    db.commit()
    
    for t in created_transcripts:
        db.refresh(t)
        
    return created_transcripts

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
