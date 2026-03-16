from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AIInsightBase(BaseModel):
    summary: Optional[str] = None
    key_points: Optional[str] = None
    suggested_questions: Optional[str] = None
    risk_flags: Optional[str] = None
    emerging_themes: Optional[str] = None
    model_name: Optional[str] = None


class AIInsightCreate(AIInsightBase):
    pass


class AIInsight(AIInsightBase):
    id: int
    consultation_id: int
    created_at: datetime

    class Config:
        from_attributes = True
