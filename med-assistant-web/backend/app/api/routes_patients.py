from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.deps import get_db, get_current_user
from app.models.patient import Patient as PatientModel
from app.schemas.patient import Patient, PatientCreate
from app.models.user import User

router = APIRouter(prefix="/patients", tags=["patients"])

@router.post("/", response_model=Patient)
def create_patient(
    payload: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Check if a patient with the same display_id already exists for this doctor (optional, but good practice)
    existing_patient = db.query(PatientModel).filter(
        PatientModel.display_id == payload.display_id
    ).first()
    if existing_patient:
        raise HTTPException(status_code=400, detail="Patient with this ID already exists")

    p = PatientModel(
        doctor_id=current_user.id,
        display_id=payload.display_id,
        name=payload.name,
        date_of_birth=payload.date_of_birth,
        gender=payload.gender,
        key_history=payload.key_history,
        created_at=datetime.utcnow(),
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p

@router.get("/", response_model=List[Patient])
def list_patients(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    qs = (
        db.query(PatientModel)
        .filter(PatientModel.doctor_id == current_user.id)
        .order_by(PatientModel.created_at.desc())
    )
    return list(qs)

@router.get("/{patient_id}", response_model=Patient)
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    p = (
        db.query(PatientModel)
        .filter(
            PatientModel.id == patient_id,
            PatientModel.doctor_id == current_user.id,
        )
        .first()
    )
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found")
    return p
