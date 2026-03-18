from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class LiveInsightBase(BaseModel):
    summary: Optional[str] = None
    key_points: Optional[str] = None
    suggested_questions: Optional[str] = None
    risk_flags: Optional[str] = None
    model_name: Optional[str] = None


class LiveInsight(LiveInsightBase):
    id: int
    consultation_id: int
    created_at: datetime

    class Config:
        from_attributes = True

