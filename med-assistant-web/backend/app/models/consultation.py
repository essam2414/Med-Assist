# backend/app/models/consultation.py
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db import Base


class Consultation(Base):
    __tablename__ = "consultations"

    id = Column(Integer, primary_key=True, index=True)

    doctor_id = Column(Integer, ForeignKey("users.id"), index=True)
    doctor = relationship("User", back_populates="consultations")

    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True, index=True)
    patient = relationship("Patient", back_populates="consultations")

    title = Column(String, nullable=False)
    status = Column(String, default="draft", index=True)
    recall_bot_id = Column(String, nullable=True, index=True)
    about = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    transcripts = relationship("TranscriptEntry", back_populates="consultation", cascade="all, delete-orphan")
    insights = relationship("AIInsight", back_populates="consultation", uselist=False, cascade="all, delete-orphan")
    live_insights = relationship("LiveInsight", back_populates="consultation", cascade="all, delete-orphan")
