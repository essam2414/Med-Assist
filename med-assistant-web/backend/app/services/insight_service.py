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

Your goal is to generate brief, non-directive insights that help the doctor understand and document the consultation.

Rules:
- Do NOT give diagnoses, treatment recommendations, or dosing advice.
- Only summarise or highlight what is explicitly present in the transcript or patient data.
- Incorporate shared decision-making principles from clinical guidelines where relevant.
- Focus on:
  1. summarising main complaints and history so far
  2. suggesting clarifications the doctor might want to ask
  3. reminding the doctor of relevant existing conditions/allergies
  4. referencing best practices for patient communication or shared decision making

You MUST respond ONLY with a valid JSON object matching this schema. Do not include any other text or markdown formatting outside the JSON:
{
  "summary": "1-3 sentences summarizing what has been said so far",
  "key_points": "A few bullet points summarizing main complaints/history",
  "suggested_questions": "A few non-directive clarifications or shared decision-making prompts",
  "risk_flags": "Relevant existing conditions, allergies, or points of clinical uncertainty"
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
    # PERFORMANCE OPTIMIZATION: Reduce k to 2 for faster context processing
    guideline_query = f"{about_text} {transcript_text[:500]}"
    relevant_guidelines = knowledge_base.query_guidelines(guideline_query, k=2)

    # 5. Construct the Prompt
    human_content = (
        f"--- CONSULTATION CONTEXT ---\n"
        f"Topic/About: {about_text}\n\n"
        f"--- PATIENT PROFILE ---\n{patient_info}\n"
        f"--- CLINICAL GUIDELINES ---\n{relevant_guidelines}\n\n"
        f"--- TRANSCRIPT---\n{transcript_text}\n"
    )

    print(f"--- Generating AI Insights for Consultation {consultation_id} ---")
    print(f"Transcript Length: {len(transcript_text)} chars{' (Truncated)' if is_truncated else ''}")
    print(f"Retrieved Guidelines from FAISS: {len(relevant_guidelines)} chars")

    # 6. Invoke the Model (matching Ask AI config)
    llm = ChatOllama(
        model="llama3.2", 
        temperature=0,
        num_predict=400,    # Optimized for speed
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
        
        # Helper to ensure we get a string back (supporting lists from AI)
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
        print("Failed to parse JSON from AI model. Raw content:", content)
        # Fallback if standard JSON mapping fails
        return {
            "summary": "AI successfully analyzed but returned improperly formatted text.",
            "key_points": str(content),
            "suggested_questions": "",
            "risk_flags": "",
            "model_name": "llama3.2"
        }
