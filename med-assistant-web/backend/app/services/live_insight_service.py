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
1. PATIENT BACKGROUND - name and known history
2. ALL PREVIOUS LIVE INSIGHTS - everything already communicated; do NOT repeat any of it
3. THE NEW TRANSCRIPT SEGMENT - lines spoken since your last update (your PRIMARY source)
4. FULL CONVERSATION SO FAR - background context only

Your job: identify what is GENUINELY NEW in section 3 that is NOT already in section 2.

━━━ RULES ━━━
GROUNDING
- Only report facts EXPLICITLY STATED in sections 3 or 4. Never infer or speculate.
- Do NOT interpret tone, emotion, or certainty unless directly quoted.
- Do NOT give diagnoses, prognoses, or medical advice.

NON-REPETITION
- A fact already in section 2 must NOT appear again, even slightly rephrased.
- If the new segment adds nothing materially new, return ALL empty strings. Silence is better than repetition.

PROBLEM-LEVEL SUMMARIES (not atomic data points)
- Under "new_problems", group related clinical facts into meaningful problem statements.
  GOOD: "Recurrent exertional central chest pain radiating to left arm, lasting 5-10 mins, relieved by rest."
  BAD:  "Location of pain: middle of the chest." / "Pain duration: 5-10 minutes."

SUMMARY (2-3 sentences)
- Sentence 1: the main complaint and its key features (location, character, radiation, timing, triggers, relief).
- Sentence 2: any associated symptoms or absence of red-flag symptoms if newly mentioned.
- Sentence 3 (optional): where in the consultation you are (e.g. "History complete; doctor has proposed ECG.").

SUGGESTIONS TO CONSIDER (max 2)
- Only suggest clarifications NOT already addressed in section 4.
- Advance logically: if location/nature/duration are documented, move to triggers, relief, associated symptoms, risk factors, impact on functioning, red flags.
- Never repeat a suggestion from section 2.

RISKS/CONTEXT
- Explicitly capture: cardiovascular risk factors (smoking, hypertension, diabetes, family history), exertional pattern, relief factors, and any red-flag symptom absences (e.g. "no nausea or sweating reported").
- Only include what is documented in sections 3 or 4.

━━━ OUTPUT ━━━
Respond ONLY with a valid JSON object. No markdown, no explanation:
{
  "summary": "2-3 sentence clinical summary of what is new, or empty string if nothing new",
  "new_problems": "1-3 bullet lines, each a clinical problem statement grouping related facts, or empty string",
  "suggestions_to_consider": "Up to 2 bullet lines of next logical clarifications not yet addressed, or empty string",
  "risks_context": "1-4 bullet lines of risk factors, red flags, and modifiers explicitly documented, or empty string"
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

        # Build the NEW segment specifically (lines added since last insight) — primary source
        new_segment_text = "\n".join([f"[{t.speaker}]: {t.text}" for t in new_transcripts])

        # Build a compact cumulative "established facts" summary from all previous insights.
        # This stays flat in size (one bullet per fact type, deduplicated) rather than
        # growing linearly with every update, which keeps the prompt token count bounded.
        all_prev_insights = db.query(LiveInsight).filter(
            LiveInsight.consultation_id == consultation_id
        ).order_by(LiveInsight.created_at.asc()).all()

        if not all_prev_insights:
            established_facts = "None - this is the first update."
        else:
            # Collect all unique lines from all previous updates
            seen = set()
            fact_lines = []
            for pi in all_prev_insights:
                for field in [pi.summary, pi.key_points, pi.suggested_questions, pi.risk_flags]:
                    if not field:
                        continue
                    for line in field.split("\n"):
                        line = line.strip()
                        if line and line.lower() not in seen:
                            seen.add(line.lower())
                            fact_lines.append(f"• {line.lstrip('- •')}")
            established_facts = "\n".join(fact_lines) if fact_lines else "None."

        # Only include the last 800 chars of transcript for bridging context.
        # The model already has the new segment and established facts — the full
        # transcript is redundant and expensive.
        all_transcripts = db.query(TranscriptEntry).filter(
            TranscriptEntry.consultation_id == consultation_id
        ).order_by(TranscriptEntry.start_time).all()
        full_transcript = "\n".join([f"[{t.speaker}]: {t.text}" for t in all_transcripts])
        bridge_context = full_transcript[-800:] if len(full_transcript) > 800 else full_transcript

        # Release database lock BEFORE the slow LLM generation process to avoid OperationalError on sync_transcripts!
        db.commit()

        # 4. PROMPTING — compact structure
        human_content = (
            f"--- 1. PATIENT BACKGROUND ---\n{patient_info}\n\n"
            f"--- 2. ESTABLISHED FACTS (do NOT repeat any of this) ---\n{established_facts}\n\n"
            f"--- 3. NEW TRANSCRIPT SEGMENT (your primary source) ---\n{new_segment_text}\n\n"
            f"--- 4. RECENT CONVERSATION CONTEXT ---\n{bridge_context}\n"
        )

        llm = ChatOllama(
            model="llama3.2",
            temperature=0,
            num_predict=400,
            num_thread=8,
            num_ctx=2048,   # Reduced: inputs are now compact so we don't need 4096
        )

        response = llm.invoke([
            SystemMessage(content=LIVE_SYSTEM_PROMPT),
            HumanMessage(content=human_content)
        ])

        # 5. PARSE AND SAVE
        try:
            # Strip any accidental markdown fences the model might add
            raw = response.content.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            parsed = json.loads(raw)
            
            def ensure_string(val):
                if isinstance(val, list):
                    return "\n".join([f"- {item}" if not str(item).startswith("-") else str(item) for item in val])
                return str(val) if val is not None else ""

            summary = ensure_string(parsed.get("summary", "")).strip()
            # Support new field names; fall back to old names for backward compat
            key_points = ensure_string(parsed.get("new_problems", parsed.get("key_points", ""))).strip()
            suggested = ensure_string(parsed.get("suggestions_to_consider", parsed.get("suggested_questions", ""))).strip()
            risks = ensure_string(parsed.get("risks_context", parsed.get("risk_flags", ""))).strip()

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
