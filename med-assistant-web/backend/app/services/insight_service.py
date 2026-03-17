import json
from sqlalchemy.orm import Session
from fastapi import HTTPException
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

from app.models.consultation import Consultation
from app.models.patient import Patient
from app.models.transcript import TranscriptEntry
from app.services.knowledge_base import knowledge_base

SYSTEM_PROMPT = """You are a senior clinical assistant producing a comprehensive post-consultation summary for a doctor.

This is activated AFTER the consultation has concluded. You have access to the full transcript, the patient's complete record, and relevant NICE clinical guidelines.

Your goal is to produce a thorough, holistic clinical overview — significantly more detailed than any real-time updates. This is a final structured handover document, not a live alert.

━━━ RULES ━━━
GROUNDING
- Only report facts EXPLICITLY present in the transcript or patient record. Do not speculate or infer.
- Do NOT give diagnoses, prescriptions, or treatment decisions — you are supporting the doctor, not replacing them.
- Where the transcript is ambiguous, note it rather than assume.

STRUCTURE
Produce four sections as described below. Each should be substantive — this is a detailed summary, not a brief alert.

1. COMPREHENSIVE SUMMARY (3-6 sentences)
   - Open with the primary presenting complaint and all its key clinical features: character, location, radiation, severity, timing, triggers, relieving/aggravating factors.
   - Cover associated symptoms and relevant negatives (e.g. no nausea, no syncope).
   - Note the relevant past medical history, medications, and social history disclosed during the consultation.
   - Close with what was discussed or decided: tests ordered, next steps, patient understanding.

2. MAIN CLINICAL PROBLEMS (3-6 bullets)
   - Write clinical problem statements — not isolated data points.
   - Each bullet should group related facts: e.g. "Exertional central chest pain radiating to left arm, 5-10 min duration, relieved by rest — consistent pattern over past week."
   - Include risk factors as separate problem statements: e.g. "Cardiovascular risk profile: hypertension on treatment, 20-pack-year smoking history."

3. CLARIFICATION PROMPTS (2-4 bullets)
   - Identify clinically important gaps NOT already addressed in the consultation.
   - Structure around SOCRATES or standard clerking: Was severity (0-10) documented? Impact on daily activities? Family cardiac history? Medication compliance?
   - Only list genuinely missing information — do not repeat what was covered.

4. RELEVANT CONTEXT & RISKS / NICE GUIDANCE (3-6 bullets)
   - List all cardiovascular or relevant risk factors disclosed: hypertension, smoking, diabetes, hyperlipidaemia, family history, obesity, etc.
   - Note any NICE-recommended steps that are relevant given the presentation — e.g. recommended investigations, referral thresholds, or safety-netting advice.
   - Include patient record data: prior diagnoses, current medications, allergies.
   - Flag any red-flag combinations that warrant urgent action according to guidelines.

━━━ OUTPUT ━━━
You MUST respond ONLY with a valid JSON object. No markdown, no explanation:
{
  "summary": "Comprehensive 3-6 sentence post-consultation summary",
  "key_points": "3-6 bullet lines, each a clinical problem statement",
  "suggested_questions": "2-4 bullet lines of unresolved clinical gaps",
  "risk_flags": "3-6 bullet lines of risk factors, comorbidities, and NICE-informed considerations"
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

    # 2. Fetch Full Structured Patient Data
    patient_info = "No patient data available (Anonymous).\n"
    
    if patient:
        patient_info = (
            f"Name: {patient.name or 'N/A'}\n"
            f"Date of Birth: {patient.date_of_birth or 'N/A'}\n"
            f"Gender: {patient.gender or 'N/A'}\n"
            f"Key History/Diagnoses: {patient.key_history or 'None'}\n"
        )

    # 3. Fetch Full Transcript (no truncation — this is a post-consultation holistic view)
    transcripts = db.query(TranscriptEntry).filter(
        TranscriptEntry.consultation_id == consultation_id
    ).order_by(TranscriptEntry.start_time).all()
    
    transcript_text = "No transcript available yet."
    if transcripts:
        transcript_text = "\n".join([f"[{t.speaker}]: {t.text}" for t in transcripts])
    
    # Apply a generous limit — this is meant to be comprehensive
    MAX_TRANSCRIPT_CHARS = 8000
    if len(transcript_text) > MAX_TRANSCRIPT_CHARS:
        transcript_text = "[... Earlier transcript omitted for length ...]\n" + transcript_text[-MAX_TRANSCRIPT_CHARS:]

    # 4. Consultation context
    about_text = consultation.about or "General consultation."

    # 5. RAG: Retrieve relevant NICE guidelines
    guideline_query = f"{about_text} {transcript_text[:600]}"
    relevant_guidelines = knowledge_base.query_guidelines(guideline_query, k=3)  # k=3 for comprehensive view

    # 6. Construct the Prompt
    human_content = (
        f"--- CONSULTATION CONTEXT ---\n"
        f"Topic: {about_text}\n\n"
        f"--- FULL CONSULTATION TRANSCRIPT ---\n{transcript_text}\n\n"
        f"--- PATIENT RECORD ---\n{patient_info}\n"
        f"--- RELEVANT NICE CLINICAL GUIDELINES ---\n{relevant_guidelines}\n"
    )

    print(f"--- Generating Post-Consultation AI Insights for Consultation {consultation_id} ---")
    
    # 7. Invoke the Model — more generous limits for a holistic summary
    llm = ChatOllama(
        model="llama3.2", 
        temperature=0,
        num_predict=700,   # More tokens for the detailed comprehensive summary
        num_thread=8,
        num_ctx=6000,      # Full context for the whole transcript
        repeat_penalty=1.2,
        keep_alive=-1
    )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=human_content)
    ]
    
    response = llm.invoke(messages)
    content = response.content

    # 8. Parse Output
    try:
        # Strip accidental markdown fences
        raw = content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        parsed_data = json.loads(raw)
        
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
