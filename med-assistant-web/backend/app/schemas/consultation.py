from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.schemas.transcript import TranscriptEntry
from app.schemas.insight import AIInsight


class ConsultationBase(BaseModel):
  title: str


class ConsultationCreate(ConsultationBase):
  pass


class Consultation(ConsultationBase):
  id: int
  created_at: datetime
  ended_at: Optional[datetime] = None
  
  transcripts: List[TranscriptEntry] = []
  insights: Optional[AIInsight] = None

  class Config:
    orm_mode = True
