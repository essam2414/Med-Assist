from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class AIAnalyticsBase(BaseModel):
    week_start_date: datetime
    consultation_count: int
    patient_count: int
    summary: Optional[str] = None
    consultation_details: Optional[List[dict]] = None
    patient_names: Optional[List[str]] = None


class AIAnalyticsCreate(AIAnalyticsBase):
    pass


class AIAnalyticsResponse(AIAnalyticsBase):
    id: int
    doctor_id: int
    created_at: datetime

    class Config:
        from_attributes = True
