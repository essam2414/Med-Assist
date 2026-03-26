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

async def generate_weekly_analytics(db: Session, doctor_id: int, doctor_name: str, target_date: date, generate_summary: bool = False):
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
            combined_text = "\n\n".join([f"Consultation {ins.consultation_id} - Issues discussed: {ins.key_points}" for ins in insights if ins.key_points])
            
            if combined_text.strip():
                llm = ChatOllama(
                    model="llama3.2",
                    temperature=0.3
                )
                
                prompt = PromptTemplate.from_template(
                    """System:

You are an assistant generating a weekly overview of the health issues discussed in a doctor's consultations.
You will be given data for EXACTLY {consultation_count} consultation(s) representing {patient_count} patient(s) for this week.
Each item describes the key acute complaints and background risk factors that were documented in that consultation.

Your task is to write a concise summary (1-2 short paragraphs) describing exactly what was seen this week.

Rules:
- If consultation_count is 1, do NOT use plural phrases. Frame the summary for a single case.
- If consultation_count is small (2 to 5), do NOT use sweeping generalizations like "many experiencing", "a common issue", or "a group of individuals". Use precise, appropriately scaled language (e.g. "one patient presented with...", "another discussed...").
- Clearly differentiate between acute, active complaints (e.g. right shoulder pain) and background risk factors (e.g. history of GERD or migraines). Do not report past history as new acute complaints.
- Base your summary ONLY on the provided issue descriptions.
- Do NOT invent additional issues, fake patterns, or fake patient populations.
- Do NOT give diagnoses, treatment recommendations, or management plans.
- Do not include greetings or sign-offs; output only the summary text.

User:

Data for Dr {doctor_name} from {week_start} to {week_end} ({consultation_count} consultations, {patient_count} patients):

{consultation_issues}
"""
                )
                chain = prompt | llm
                try:
                    response = chain.invoke({
                        "doctor_name": doctor_name or "Doctor",
                        "week_start": week_start.strftime("%B %d, %Y"),
                        "week_end": week_end.strftime("%B %d, %Y"),
                        "consultation_issues": combined_text,
                        "consultation_count": consultation_count,
                        "patient_count": patient_count
                    })
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

