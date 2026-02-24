# backend/app/models/transcript.py
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Float
from sqlalchemy.orm import relationship

from app.db import Base


class TranscriptEntry(Base):
    __tablename__ = "transcript_entries"

    id = Column(Integer, primary_key=True, index=True)
    consultation_id = Column(Integer, ForeignKey("consultations.id"), index=True)
    speaker = Column(String, default="unknown")
    start_time = Column(Float, default=0.0)
    end_time = Column(Float, nullable=True)
    text = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    consultation = relationship("Consultation", back_populates="transcripts")
