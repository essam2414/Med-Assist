from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ConsultationBase(BaseModel):
  title: str


class ConsultationCreate(ConsultationBase):
  pass


class Consultation(ConsultationBase):
  id: int
  created_at: datetime
  ended_at: Optional[datetime] = None

  class Config:
    orm_mode = True
