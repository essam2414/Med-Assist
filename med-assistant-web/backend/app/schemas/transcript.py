from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TranscriptEntryBase(BaseModel):
    speaker: str
    start_time: float
    end_time: Optional[float] = None
    text: str


class TranscriptEntryCreate(TranscriptEntryBase):
    pass


class TranscriptEntry(TranscriptEntryBase):
    id: int
    consultation_id: int
    created_at: datetime

    class Config:
        orm_mode = True
