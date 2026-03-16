import json
from sqlalchemy.orm import Session
from fastapi import HTTPException
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

from app.models.consultation import Consultation
from app.models.patient import Patient
from app.models.transcript import TranscriptEntry
from app.services.knowledge_base import knowledge_base

SYSTEM_PROMPT = """You are an assistant for clinicians during a live consultation.

Your goal is to generate structured, brief, and non-directive insights.

Rules:
- Do NOT give diagnoses, treatment recommendations, or dosing advice.
- Only summarise or highlight what is explicitly present in the transcript or patient record.
- Incorporate shared decision-making and patient experience principles from NICE guidelines.

Output Format:
1. Summary: 1-3 sentences summarising what has been discussed so far. Neutral and factual.
2. Main problems mentioned today: 3-5 short bullet points max.
3. Clarification prompts (for you to consider): 2-4 bullet points about missing standard details (onset, duration, severity, impact, red flags). Use standard structures (e.g., SOCRATES).
4. Relevant Context / Risks: List prior diagnoses, meds, and allergies from the record.

You MUST respond ONLY with a valid JSON object. Do not include markdown formatting:
{
  "summary": "Summary text",
  "key_points": "Bullet list for Main problems",
  "suggested_questions": "Bullet list for Clarification prompts",
  "risk_flags": "Bullet list for Relevant Context / Risks"
}
"""

def generate_live_insights(consultation_id: int, db: Session, doctor_id: int):
    # 1. Fetch Consultation
    consultation = db.query(Consultation).filter(
        Consultation.id == consultation_id,
        Consultation.doctor_id == doctor_id
    ).first()
    
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")

    patient = consultation.patient

    # 2. Fetch Structured Patient Data
    patient_info = "No patient data available (Anonymous)."
    
    if patient:
        patient_info = (
            f"Patient Name: {patient.name or 'N/A'}\n"
            f"Age/DOB: {patient.date_of_birth or 'N/A'}\n"
            f"Gender: {patient.gender or 'N/A'}\n"
            f"Key History/Diagnoses: {patient.key_history or 'None'}\n"
        )

    # 3. Fetch Transcripts
    transcripts = db.query(TranscriptEntry).filter(
        TranscriptEntry.consultation_id == consultation_id
    ).order_by(TranscriptEntry.start_time).all()
    
    transcript_text = "No transcript available yet."
    if transcripts:
        transcript_text = "\n".join([f"[{t.speaker}]: {t.text}" for t in transcripts])
    
    # --- PERFORMANCE OPTIMIZATION: Transcript Windowing ---
    MAX_TRANSCRIPT_CHARS = 6000
    is_truncated = False
    if len(transcript_text) > MAX_TRANSCRIPT_CHARS:
        transcript_text = "[... Earlier transcript omitted for speed ...]\n" + transcript_text[-MAX_TRANSCRIPT_CHARS:]
        is_truncated = True

    # 3b. Consultation About
    about_text = consultation.about or "Not specified."

    # 4. Fetch Relevant Guidelines (RAG)
    # PERFORMANCE OPTIMIZATION: k=2 for speed
    guideline_query = f"{about_text} {transcript_text[:500]}"
    relevant_guidelines = knowledge_base.query_guidelines(guideline_query, k=2)

    # 5. Construct the Prompt
    human_content = (
        f"--- CURRENT CONSULTATION ---\n"
        f"Topic/About: {about_text}\n"
        f"Transcript Segment: \n{transcript_text}\n\n"
        f"--- PATIENT RECORD ---\n{patient_info}\n"
        f"--- REFERENCE CLINICAL GUIDELINES ---\n{relevant_guidelines}\n"
    )

    print(f"--- Generating Optimized AI Insights for Consultation {consultation_id} ---")
    
    # 6. Invoke the Model
    llm = ChatOllama(
        model="llama3.2", 
        temperature=0,
        num_predict=400,
        num_thread=8,
        num_ctx=4096,
        repeat_penalty=1.2,
        keep_alive=-1
    )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=human_content)
    ]
    
    response = llm.invoke(messages)
    content = response.content

    # 6. Parse Output
    try:
        parsed_data = json.loads(content)
        
        def ensure_string(val):
            if isinstance(val, list):
                return "\n".join([f"- {item}" if not str(item).startswith("-") else str(item) for item in val])
            return str(val) if val is not None else ""

        return {
            "summary": ensure_string(parsed_data.get("summary", "")),
            "key_points": ensure_string(parsed_data.get("key_points", "")),
            "suggested_questions": ensure_string(parsed_data.get("suggested_questions", "")),
            "risk_flags": ensure_string(parsed_data.get("risk_flags", "")),
            "model_name": "llama3.2"
        }
    except json.JSONDecodeError:
        print("Failed to parse JSON. Raw content:", content)
        return {
            "summary": "Error parsing AI output.",
            "key_points": str(content),
            "suggested_questions": "",
            "risk_flags": "",
            "model_name": "llama3.2"
        }
