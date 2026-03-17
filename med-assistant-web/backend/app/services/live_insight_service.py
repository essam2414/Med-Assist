import json
from datetime import datetime
from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from app.models.consultation import Consultation
from app.models.transcript import TranscriptEntry
from app.models.live_insight import LiveInsight
from app.db import SessionLocal

# Global set to track consultations currently generating insights
PROCESSING_CONSULTATIONS = set()

LIVE_SYSTEM_PROMPT = """You are a real-time clinical assistant helping a doctor during a live patient consultation.

You will receive:
1. PATIENT BACKGROUND - Name and known history
2. ALL PREVIOUS LIVE INSIGHTS - everything you have already communicated to the doctor
3. THE NEW TRANSCRIPT SEGMENT - the specific new lines spoken since your last update
4. FULL CONVERSATION SO FAR - for context only

Your **only** job is to identify what is GENUINELY NEW in the NEW TRANSCRIPT SEGMENT that has NOT already been covered in the ALL PREVIOUS LIVE INSIGHTS.

STRICT RULES:
- Only report facts that are EXPLICITLY STATED in the NEW TRANSCRIPT SEGMENT. Do NOT infer, speculate or interpret tone/emotion.
- If a fact was already in the previous insights, DO NOT mention it again, even slightly rephrased.
- "To Consider" must only be questions / actions NOT already addressed by the doctor in the full conversation.
- If the new segment adds nothing materially new (e.g. it's just the doctor ordering a test already mentioned), return ALL empty strings. It is better to return nothing than to repeat.
- Do NOT give diagnoses, prognoses or medical advice.
- Keep each bullet to one concise line.

Output Format: You MUST respond ONLY with a valid JSON object, no markdown, no explanation:
{
  "summary": "One sentence on the single most important NEW topic from this segment, or empty string",
  "key_points": "1-2 bullet lines of NEW clinical facts (symptoms, history, medications), or empty string",
  "suggested_questions": "1-2 bullet lines for follow-up the doctor has NOT yet asked, or empty string",
  "risk_flags": "1-2 bullet lines of NEW risk factors or red flags explicitly mentioned, or empty string"
}
"""

def evaluate_and_generate_live_insights(consultation_id: int):
    """
    Background worker that checks if a new live insight should be generated,
    and if so, calls the LLM and saves it.
    """
    if consultation_id in PROCESSING_CONSULTATIONS:
        print(f"[{consultation_id}] LIVE: Already processing. Skipping.")
        return

    PROCESSING_CONSULTATIONS.add(consultation_id)
    
    # Create an independent DB session for the background task
    db: Session = SessionLocal()
    try:
        consultation = db.query(Consultation).filter(Consultation.id == consultation_id).first()
        if not consultation or consultation.status != "draft":
            if consultation and consultation.status != "draft":
                print(f"[{consultation_id}] LIVE: Skipping. Consultation is {consultation.status}.")
            return

        patient = consultation.patient

        # Find the last generated live insight
        last_insight = db.query(LiveInsight).filter(
            LiveInsight.consultation_id == consultation_id
        ).order_by(LiveInsight.created_at.desc()).first()

        # 1. THROTTLING
        # Do not generate if we generated one less than 20 seconds ago
        if last_insight:
            time_diff = (datetime.utcnow() - last_insight.created_at).total_seconds()
            if time_diff < 12:
                print(f"[{consultation_id}] LIVE: Skipping. Last insight was {time_diff:.1f}s ago (min 12s).")
                return

        # 2. TRANSCRIPT LENGTH CHECK
        # Check how much transcript has been added since the last insight
        query = db.query(TranscriptEntry).filter(TranscriptEntry.consultation_id == consultation_id)
        if last_insight:
            query = query.filter(TranscriptEntry.created_at > last_insight.created_at)
        
        new_transcripts = query.order_by(TranscriptEntry.start_time).all()
        new_text_len = sum(len(t.text) for t in new_transcripts)

        # Require at least 120 characters of new audio to bother running the LLM
        if new_text_len < 120:
            print(f"[{consultation_id}] LIVE: Skipping. Not enough new transcript length ({new_text_len} < 120).")
            return

        print(f"[{consultation_id}] LIVE: Generating new live insight based on {new_text_len} chars of new audio...")

        # 3. CONTEXT GATHERING
        patient_info = "No patient data available."
        if patient:
            patient_info = (
                f"Name: {patient.name or 'N/A'}, "
                f"History: {patient.key_history or 'None'}"
            )

        # Build the full conversation transcript for background context
        all_transcripts = db.query(TranscriptEntry).filter(
            TranscriptEntry.consultation_id == consultation_id
        ).order_by(TranscriptEntry.start_time).all()
        
        full_transcript = "\n".join([f"[{t.speaker}]: {t.text}" for t in all_transcripts])
        # Trim to last 6000 chars to stay within context window
        full_transcript_window = full_transcript[-6000:] if len(full_transcript) > 6000 else full_transcript

        # Build the NEW segment specifically (lines added since last insight)
        new_segment_text = "\n".join([f"[{t.speaker}]: {t.text}" for t in new_transcripts])

        # Get ALL previous live insights (not just 3) so the model can diff fully
        all_prev_insights = db.query(LiveInsight).filter(
            LiveInsight.consultation_id == consultation_id
        ).order_by(LiveInsight.created_at.asc()).all()

        previous_insights_text = "None - this is the first update."
        if all_prev_insights:
            prev_texts = []
            for i, pi in enumerate(all_prev_insights):
                parts = []
                if pi.summary: parts.append(f"  Summary: {pi.summary}")
                if pi.key_points: parts.append(f"  Key Points: {pi.key_points}")
                if pi.suggested_questions: parts.append(f"  To Consider: {pi.suggested_questions}")
                if pi.risk_flags: parts.append(f"  Risks: {pi.risk_flags}")
                if parts:
                    prev_texts.append(f"[Update {i+1}]\n" + "\n".join(parts))
            previous_insights_text = "\n\n".join(prev_texts)

        # 4. PROMPTING — structured to match the new system prompt
        human_content = (
            f"--- 1. PATIENT BACKGROUND ---\n{patient_info}\n\n"
            f"--- 2. ALL PREVIOUS LIVE INSIGHTS (do NOT repeat any of this) ---\n{previous_insights_text}\n\n"
            f"--- 3. THE NEW TRANSCRIPT SEGMENT (your primary source for new insights) ---\n{new_segment_text}\n\n"
            f"--- 4. FULL CONVERSATION SO FAR (background context only) ---\n{full_transcript_window}\n"
        )

        llm = ChatOllama(
            model="llama3.2", 
            temperature=0,
            num_predict=300,  # Keep responses tight
            num_thread=8,
            num_ctx=4096
        )

        response = llm.invoke([
            SystemMessage(content=LIVE_SYSTEM_PROMPT),
            HumanMessage(content=human_content)
        ])

        # 5. PARSE AND SAVE
        try:
            parsed = json.loads(response.content)
            
            def ensure_string(val):
                if isinstance(val, list):
                    return "\n".join([f"- {item}" if not str(item).startswith("-") else str(item) for item in val])
                return str(val) if val is not None else ""

            summary = ensure_string(parsed.get("summary", "")).strip()
            key_points = ensure_string(parsed.get("key_points", "")).strip()
            suggested = ensure_string(parsed.get("suggested_questions", "")).strip()
            risks = ensure_string(parsed.get("risk_flags", "")).strip()

            # If all are empty, the model found nothing new to say, don't clatter the DB
            if not any([summary, key_points, suggested, risks]):
                print(f"[{consultation_id}] LIVE: Model generated empty insights. Skipping DB save.")
                return

            new_insight = LiveInsight(
                consultation_id=consultation_id,
                summary=summary,
                key_points=key_points,
                suggested_questions=suggested,
                risk_flags=risks,
                model_name="llama3.2"
            )
            db.add(new_insight)
            db.commit()
            print(f"[{consultation_id}] LIVE: Saved new live insight!")

        except json.JSONDecodeError:
            print(f"[{consultation_id}] LIVE: Failed to parse JSON. Raw:", response.content)

    except Exception as e:
        print(f"[{consultation_id}] LIVE: Error evaluating insights: {e}")
    finally:
        db.close()
        if consultation_id in PROCESSING_CONSULTATIONS:
            PROCESSING_CONSULTATIONS.remove(consultation_id)
