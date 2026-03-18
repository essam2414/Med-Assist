from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, JSON
from sqlalchemy.orm import relationship

from app.db import Base


class AIAnalytics(Base):
    __tablename__ = "ai_analytics"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("users.id"), index=True)
    doctor = relationship("User", back_populates="ai_analytics")

    week_start_date = Column(DateTime, nullable=False, index=True)
    consultation_count = Column(Integer, default=0)
    patient_count = Column(Integer, default=0)
    summary = Column(String, nullable=True)
    
    # Store JSON lists/dicts for counts
    consultation_details = Column(JSON, nullable=True) # [{"id": 1, "title": "..."}]
    patient_names = Column(JSON, nullable=True)     # ["John Doe", "Anonymous"]
    
    created_at = Column(DateTime, default=datetime.utcnow)
