from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.deps import get_db, get_current_user
from app.models.insight import AIInsight as InsightModel
from app.models.consultation import Consultation as ConsultationModel
from app.schemas.insight import AIInsight, AIInsightCreate
from app.models.user import User

router = APIRouter(prefix="/insights", tags=["insights"])

@router.post("/", response_model=AIInsight)
def create_insight(
    payload: AIInsightCreate,
    consultation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    consultation = db.query(ConsultationModel).filter(
        ConsultationModel.id == consultation_id,
        ConsultationModel.doctor_id == current_user.id
    ).first()
    
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")
        
    # Check if an insight already exists for this consultation
    existing_insight = db.query(InsightModel).filter(InsightModel.consultation_id == consultation_id).first()
    if existing_insight:
        raise HTTPException(status_code=400, detail="Insight already exists for this consultation")

    i = InsightModel(
        consultation_id=consultation.id,
        summary=payload.summary,
        key_points=payload.key_points,
        suggested_questions=payload.suggested_questions,
        risk_flags=payload.risk_flags,
        model_name=payload.model_name,
        created_at=datetime.utcnow(),
    )
    db.add(i)
    db.commit()
    db.refresh(i)
    return i

@router.get("/", response_model=List[AIInsight])
def list_insights(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    qs = (
        db.query(InsightModel)
        .join(ConsultationModel)
        .filter(ConsultationModel.doctor_id == current_user.id)
        .order_by(InsightModel.created_at.desc())
    )
    return list(qs)

@router.get("/{id}", response_model=AIInsight)
def get_insight(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    i = (
        db.query(InsightModel)
        .join(ConsultationModel)
        .filter(
            InsightModel.id == id,
            ConsultationModel.doctor_id == current_user.id
        )
        .first()
    )
    if not i:
        raise HTTPException(status_code=404, detail="Insight not found")
    return i

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_insight(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    i = (
        db.query(InsightModel)
        .join(ConsultationModel)
        .filter(
            InsightModel.id == id,
            ConsultationModel.doctor_id == current_user.id
        )
        .first()
    )
    if not i:
        raise HTTPException(status_code=404, detail="Insight not found")
        
    db.delete(i)
    db.commit()
    return None
