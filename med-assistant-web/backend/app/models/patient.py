# backend/app/models/patient.py
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Date, Text
from sqlalchemy.orm import relationship

from app.db import Base


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("users.id"), index=True)
    display_id = Column(String, unique=True, index=True)
    name = Column(String, nullable=True)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String, nullable=True)
    key_history = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    doctor = relationship("User", back_populates="patients")
    consultations = relationship("Consultation", back_populates="patient")
