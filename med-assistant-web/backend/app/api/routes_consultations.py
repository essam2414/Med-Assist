from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
from typing import List

from app.deps import get_db, get_current_user
from app.models.consultation import Consultation as ConsultationModel
from app.schemas.consultation import Consultation, ConsultationCreate
from app.models.user import User

router = APIRouter(prefix="/consultations", tags=["consultations"])


@router.post("/", response_model=Consultation)
def create_consultation(
    payload: ConsultationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    c = ConsultationModel(
        title=payload.title,
        doctor_id=current_user.id,
        status="draft",
        created_at=datetime.utcnow(),
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@router.get("/", response_model=List[Consultation])
def list_consultations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    qs = (
        db.query(ConsultationModel)
        .options(joinedload(ConsultationModel.transcripts), joinedload(ConsultationModel.insights))
        .filter(ConsultationModel.doctor_id == current_user.id)
        .order_by(ConsultationModel.created_at.desc())
    )
    return list(qs)
@router.delete("/{consultation_id}")
def delete_consultation(
    consultation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    c = (
        db.query(ConsultationModel)
        .filter(
            ConsultationModel.id == consultation_id,
            ConsultationModel.doctor_id == current_user.id,
        )
        .first()
    )
    if not c:
        raise HTTPException(status_code=404, detail="Consultation not found")

    db.delete(c)
    db.commit()
    return {"status": "ok"}


@router.patch("/{consultation_id}")
def update_consultation(
    consultation_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    c = (
        db.query(ConsultationModel)
        .filter(
            ConsultationModel.id == consultation_id,
            ConsultationModel.doctor_id == current_user.id,
        )
        .first()
    )
    if not c:
        raise HTTPException(status_code=404, detail="Consultation not found")
    
    if "status" in payload:
        c.status = payload["status"]
        if payload["status"] == "completed":
            c.ended_at = datetime.utcnow()
    
    db.commit()
    db.refresh(c)
    return c


@router.get("/active")
def get_active_consultation(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    c = (
        db.query(ConsultationModel)
        .options(joinedload(ConsultationModel.transcripts), joinedload(ConsultationModel.insights))
        .filter(
            ConsultationModel.doctor_id == current_user.id,
            ConsultationModel.status == "draft" # Or "active"
        )
        .order_by(ConsultationModel.created_at.desc())
        .first()
    )
    return c
