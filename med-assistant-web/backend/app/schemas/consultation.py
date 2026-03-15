from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.schemas.transcript import TranscriptEntry
from app.schemas.insight import AIInsight
from app.schemas.patient import Patient


class ConsultationBase(BaseModel):
  title: str
  patient_id: Optional[int] = None
  about: Optional[str] = None


class ConsultationCreate(ConsultationBase):
  pass


class Consultation(ConsultationBase):
  id: int
  status: str
  created_at: datetime
  ended_at: Optional[datetime] = None
  recall_bot_id: Optional[str] = None
  
  transcripts: List[TranscriptEntry] = []
  insights: Optional[AIInsight] = None
  patient: Optional[Patient] = None

  class Config:
    from_attributes = True
