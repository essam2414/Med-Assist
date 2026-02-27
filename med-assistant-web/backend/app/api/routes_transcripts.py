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
from app.services.stt_service import transcribe_audio_async
import asyncio

router = APIRouter(prefix="/transcripts", tags=["transcripts"])

@router.post("/upload", response_model=List[TranscriptEntry])
async def upload_and_transcribe(
    audio_file: UploadFile = File(...),
    mic_file: UploadFile = File(...),
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
        
    transcript_segments = []

    # Write both uploaded files to disk simultaneously
    # Process audio_file (Patient/Others)
    suffix_audio = os.path.splitext(audio_file.filename)[1] if audio_file.filename else ".webm"
    temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=suffix_audio)
    temp_audio.write(await audio_file.read())
    temp_path_audio = temp_audio.name
    temp_audio.close()
        
    # Process mic_file (Doctor)
    suffix_mic = os.path.splitext(mic_file.filename)[1] if mic_file.filename else ".webm"
    temp_mic = tempfile.NamedTemporaryFile(delete=False, suffix=suffix_mic)
    temp_mic.write(await mic_file.read())
    temp_path_mic = temp_mic.name
    temp_mic.close()

    try:
        # Run both transcriptions concurrently
        coro_audio = transcribe_audio_async(temp_path_audio, speaker_name="Patient/System")
        coro_mic = transcribe_audio_async(temp_path_mic, speaker_name="Doctor")
        
        results = await asyncio.gather(coro_audio, coro_mic, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                raise HTTPException(status_code=500, detail=f"Error transcribing audio: {str(result)}")
            transcript_segments.extend(result)
            
    finally:
        # Cleanup temp files
        if os.path.exists(temp_path_audio):
            os.remove(temp_path_audio)
        if os.path.exists(temp_path_mic):
            os.remove(temp_path_mic)

    # Sort interleaved segments by start time
    transcript_segments.sort(key=lambda x: x["start_time"])

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
