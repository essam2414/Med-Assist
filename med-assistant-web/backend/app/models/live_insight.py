# backend/app/models/live_insight.py
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db import Base


class LiveInsight(Base):
    __tablename__ = "live_insights"

    id = Column(Integer, primary_key=True, index=True)
    consultation_id = Column(Integer, ForeignKey("consultations.id", ondelete="CASCADE"), nullable=False)
    summary = Column(Text, nullable=True)
    key_points = Column(Text, nullable=True)
    suggested_questions = Column(Text, nullable=True)
    risk_flags = Column(Text, nullable=True)
    model_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    consultation = relationship("Consultation", back_populates="live_insights")

