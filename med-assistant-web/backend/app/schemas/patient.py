from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional

class PatientBase(BaseModel):
    display_id: str
    name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    key_history: Optional[str] = None

class PatientCreate(PatientBase):
    pass

class PatientUpdate(BaseModel):
    name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    key_history: Optional[str] = None

class Patient(PatientBase):
    id: int
    doctor_id: int
    created_at: datetime

    class Config:
        from_attributes = True
