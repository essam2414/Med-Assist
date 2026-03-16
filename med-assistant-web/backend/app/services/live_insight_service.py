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

LIVE_SYSTEM_PROMPT = """You are a real-time clinical assistant monitoring a live consultation.

Your goal is to generate *incremental, non-repetitive* insights based on the *latest* transcript segment.
You will be provided with the last few minutes of conversation, as well as the previous insights you have already generated.

Rules:
- Do NOT repeat points that are already in the "Previously Generated Insights".
- Only output NEW, explicitly stated problems, concerns, or context from the latest transcript.
- Keep it extremely brief. Bullet points only.
- Do NOT give diagnoses or medical advice.
- If there is nothing significantly new to report, return empty strings for the fields.

Output Format: You MUST respond ONLY with a valid JSON object:
{
  "summary": "1 very brief sentence summarizing the *new* topic of discussion (or empty if none)",
  "key_points": "1-2 short bullet points of *new* main problems (or empty if none)",
  "suggested_questions": "1-2 short bullet points for *new* clarification prompts for the doctor (or empty if none)",
  "risk_flags": "1-2 short bullet points of *new* context/risks mentioned (or empty if none)"
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
        if not consultation:
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

        # Require at least 70 characters of new audio to bother running the LLM
        if new_text_len < 70:
            print(f"[{consultation_id}] LIVE: Skipping. Not enough new transcript length ({new_text_len} < 70).")
            return

        print(f"[{consultation_id}] LIVE: Generating new live insight based on {new_text_len} chars of new audio...")

        # 3. CONTEXT GATHERING
        patient_info = "No patient data available."
        if patient:
            patient_info = (
                f"Name: {patient.name or 'N/A'}, "
                f"History: {patient.key_history or 'None'}"
            )

        # Get the recent context window (last 5000 chars of overall transcript)
        all_transcripts = db.query(TranscriptEntry).filter(
            TranscriptEntry.consultation_id == consultation_id
        ).order_by(TranscriptEntry.start_time).all()
        
        full_transcript = "\n".join([f"[{t.speaker}]: {t.text}" for t in all_transcripts])
        recent_transcript = full_transcript[-5000:] if len(full_transcript) > 5000 else full_transcript

        # Get the last 3 live insights to avoid repetition
        recent_insights = db.query(LiveInsight).filter(
            LiveInsight.consultation_id == consultation_id
        ).order_by(LiveInsight.created_at.desc()).limit(3).all()
        
        previous_insights_text = "None."
        if recent_insights:
            # Reverse to be chronological
            prev_texts = []
            for i, pi in enumerate(reversed(recent_insights)):
                prev_texts.append(f"--- Previous Insight {i+1} ---\nSummary: {pi.summary}\nKey Points: {pi.key_points}")
            previous_insights_text = "\n".join(prev_texts)

        # 4. PROMPTING
        human_content = (
            f"--- PATIENT --- {patient_info}\n\n"
            f"--- PREVIOUSLY GENERATED INSIGHTS (DO NOT REPEAT THESE) ---\n{previous_insights_text}\n\n"
            f"--- RECENT TRANSCRIPT WINDOW ---\n{recent_transcript}\n"
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
