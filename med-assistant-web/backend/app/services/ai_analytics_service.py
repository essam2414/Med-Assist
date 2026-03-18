# backend/app/services/ai_analytics_service.py
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from app.models.consultation import Consultation
from app.models.ai_analytics import AIAnalytics
from app.models.insight import AIInsight
from app.core.config import settings

def get_week_start(d: date) -> datetime:
    """Returns the Monday of the week for the given date."""
    dt = datetime.combine(d, datetime.min.time())
    return dt - timedelta(days=dt.weekday())

async def generate_weekly_analytics(db: Session, doctor_id: int, target_date: date, generate_summary: bool = False):
    week_start = get_week_start(target_date)
    week_end = week_start + timedelta(days=7)

    # 1. Fetch consultations for the week
    from sqlalchemy.orm import joinedload
    consultations = db.query(Consultation).options(joinedload(Consultation.patient)).filter(
        Consultation.doctor_id == doctor_id,
        Consultation.created_at >= week_start,
        Consultation.created_at < week_end,
        Consultation.status == 'completed'
    ).all()

    consultation_count = len(consultations)

    # 2. Extract details
    patient_names = set()
    anonymous_count = 0
    c_details = []
    
    for c in consultations:
        c_details.append({"id": c.id, "title": c.title or f"Consultation #{c.id}"})
        if c.patient:
            patient_names.add(c.patient.name or "Unnamed Patient")
        else:
            anonymous_count += 1
            
    patient_count = len(patient_names) + anonymous_count
    final_patient_list = list(patient_names)
    if anonymous_count > 0:
        final_patient_list.append(f"{anonymous_count} Anonymous Patients")

    # 3. Check for existing record
    analytics_record = db.query(AIAnalytics).filter(
        AIAnalytics.doctor_id == doctor_id,
        AIAnalytics.week_start_date == week_start
    ).first()

    summary_text = analytics_record.summary if analytics_record and analytics_record.summary else ""

    # 4. Generate summary using existing insights if requested
    if generate_summary:
        if consultation_count > 0:
            c_ids = [c.id for c in consultations]
            insights = db.query(AIInsight).filter(AIInsight.consultation_id.in_(c_ids)).all()
            combined_text = "\n".join([f"- {ins.key_points}" for ins in insights if ins.key_points])
            
            if combined_text.strip():
                llm = ChatOllama(
                    model="llama3.2",
                    temperature=0.3
                )
                
                prompt = PromptTemplate.from_template(
                    """You are an expert medical assistant compiling a weekly report for a doctor.
Based on the following key issues discussed in their consultations this week:
{consultation_data}

Provide a concise, conclusive summary (1-2 paragraphs) of the main health issues and trends seen across the patients this week. Look for patterns if any exist, but do not invent them.
Do not include any greeting or closing, just the summary text.
"""
                )
                chain = prompt | llm
                try:
                    response = chain.invoke({"consultation_data": combined_text})
                    summary_text = response.content.strip() if hasattr(response, 'content') else str(response)
                except Exception as e:
                    print(f"Error generating weekly summary: {e}")
                    summary_text = "Failed to generate AI summary. Please check Ollama connection."
            else:
                summary_text = "No insights available for these consultations to summarize."
        else:
            summary_text = "No completed consultations recorded for this week."

    if not analytics_record:
        analytics_record = AIAnalytics(
            doctor_id=doctor_id,
            week_start_date=week_start
        )
        db.add(analytics_record)

    analytics_record.consultation_count = consultation_count
    analytics_record.patient_count = patient_count
    analytics_record.summary = summary_text
    analytics_record.consultation_details = c_details
    analytics_record.patient_names = final_patient_list
    
    db.commit()
    db.refresh(analytics_record)
    
    return analytics_record

