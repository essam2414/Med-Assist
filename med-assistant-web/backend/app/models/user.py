# backend/app/models/user.py
from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    role = Column(String, default="doctor", index=True)  # "doctor", "admin", etc.
    hashed_password = Column(String, nullable=False)
    specialty = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    consultations = relationship("Consultation", back_populates="doctor", cascade="all, delete-orphan")
    patients = relationship("Patient", back_populates="doctor", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
