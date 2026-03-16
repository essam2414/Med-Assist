# backend/app/models/insight.py
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db import Base


class AIInsight(Base):
    __tablename__ = "ai_insights"

    id = Column(Integer, primary_key=True, index=True)
    consultation_id = Column(Integer, ForeignKey("consultations.id"), unique=True)
    summary = Column(Text, nullable=True)
    key_points = Column(Text, nullable=True)          # JSON or newline text later
    suggested_questions = Column(Text, nullable=True) # JSON or text
    risk_flags = Column(Text, nullable=True)
    emerging_themes = Column(Text, nullable=True)
    model_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    consultation = relationship("Consultation", back_populates="insights")
