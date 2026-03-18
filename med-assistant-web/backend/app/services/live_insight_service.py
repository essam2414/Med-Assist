import json
import time
from datetime import datetime
from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from app.models.consultation import Consultation
from app.models.transcript import TranscriptEntry
from app.models.live_insight import LiveInsight
from app.db import SessionLocal
from app.services.knowledge_base import knowledge_base

# Global set to track consultations currently generating insights
PROCESSING_CONSULTATIONS = set()

# Cache: consultation_id → relevant NICE guideline text
# Populated once on first insight, reused for all subsequent updates.
GUIDELINE_CACHE: dict = {}

LIVE_SYSTEM_PROMPT = """You are a real-time clinical assistant during a live consultation.

Sections provided: 1=Patient Background, 2=Your Last Insight (JSON), 3=Established Facts, 4=New Transcript (PRIMARY), 5=Full Conversation, 6=NICE Guidelines.

Your job: report ONLY what is GENUINELY NEW in section 4, not in sections 2/3.

GROUNDING
- Only report symptoms/risk factors EXPLICITLY STATED in the transcript or patient record.
- Unmentioned symptoms are "not documented" — never say "absent" or "not present".
- Never introduce terms (e.g. vomiting, diabetes) not in the text.
- No diagnoses, prognoses, or medical advice.

NON-REPETITION
- Nothing from sections 2/3 may reappear, even rephrased.
- If nothing new, return ALL empty strings.

NEW PROBLEMS: group related facts into problem statements (not atomic data points). Only NEW ones.

SUMMARY: 2-3 sentences of ONLY new information from section 4.

SUGGESTIONS (max 2): check section 5 for already-answered questions. Only suggest genuinely unaddressed gaps.

RISKS/CONTEXT:
- Only risk factors explicitly stated (quote what was said).
- Prefix guideline points with "NICE:" — never repeat from previous updates.

Respond ONLY with valid JSON:
{"summary":"","new_problems":"","suggestions_to_consider":"","risks_context":""}
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

        # Query all previous insights ONCE — used for throttling, last-insight JSON, and established facts
        all_prev_insights = db.query(LiveInsight).filter(
            LiveInsight.consultation_id == consultation_id
        ).order_by(LiveInsight.created_at.asc()).all()
        last_insight = all_prev_insights[-1] if all_prev_insights else None

        # 1. THROTTLING
        if last_insight:
            time_diff = (datetime.utcnow() - last_insight.created_at).total_seconds()
            if time_diff < 12:
                print(f"[{consultation_id}] LIVE: Skipping. Last insight was {time_diff:.1f}s ago (min 12s).")
                return

        # 2. TRANSCRIPT LENGTH CHECK
        query = db.query(TranscriptEntry).filter(TranscriptEntry.consultation_id == consultation_id)
        if last_insight:
            query = query.filter(TranscriptEntry.created_at > last_insight.created_at)
        
        new_transcripts = query.order_by(TranscriptEntry.start_time).all()
        new_text_len = sum(len(t.text) for t in new_transcripts)

        if new_text_len < 120:
            print(f"[{consultation_id}] LIVE: Skipping. Not enough new transcript ({new_text_len} < 120 chars).")
            return

        print(f"[{consultation_id}] LIVE: Generating insight from {new_text_len} chars of new audio...")
        gen_start = time.time()

        # 3. CONTEXT GATHERING
        patient_info = "No patient data available."
        if patient:
            patient_info = (
                f"Name: {patient.name or 'N/A'}, "
                f"History: {patient.key_history or 'None'}"
            )

        # Build the NEW segment specifically (lines added since last insight) — primary source
        new_segment_text = "\n".join([f"[{t.speaker}]: {t.text}" for t in new_transcripts])

        # Build the LAST INSIGHT as compact JSON so the model sees exactly what it said
        last_insight_json = "None — first update."
        if last_insight:
            last_insight_json = json.dumps({
                "summary": last_insight.summary or "",
                "new_problems": last_insight.key_points or "",
                "suggestions_to_consider": last_insight.suggested_questions or "",
                "risks_context": last_insight.risk_flags or ""
            })

        # Build a compact cumulative "established facts" summary from all previous insights.
        if not all_prev_insights:
            established_facts = "None - this is the first update."
        else:
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

        # Include more transcript context (2000 chars) so the model can see what
        # questions have already been asked and answered — critical for gap-aware suggestions.
        all_transcripts = db.query(TranscriptEntry).filter(
            TranscriptEntry.consultation_id == consultation_id
        ).order_by(TranscriptEntry.start_time).all()
        full_transcript = "\n".join([f"[{t.speaker}]: {t.text}" for t in all_transcripts])
        conversation_context = full_transcript[-2000:] if len(full_transcript) > 2000 else full_transcript

        # 4. NICE GUIDELINES (cached per consultation — RAG runs once only)
        if consultation_id not in GUIDELINE_CACHE:
            about_text = consultation.about or ""
            guideline_query = f"{about_text} {new_segment_text[:400]}"
            GUIDELINE_CACHE[consultation_id] = knowledge_base.query_guidelines(guideline_query, k=2)
            print(f"[{consultation_id}] LIVE: NICE guidelines cached.")
        relevant_guidelines = GUIDELINE_CACHE[consultation_id]

        # 5. PROMPTING — 6-section structure matching the system prompt
        human_content = (
            f"--- 1. PATIENT BACKGROUND ---\n{patient_info}\n\n"
            f"--- 2. YOUR LAST INSIGHT (do NOT repeat) ---\n{last_insight_json}\n\n"
            f"--- 3. ALL ESTABLISHED FACTS (do NOT repeat any of this) ---\n{established_facts}\n\n"
            f"--- 4. NEW TRANSCRIPT SEGMENT (your primary source) ---\n{new_segment_text}\n\n"
            f"--- 5. FULL CONVERSATION SO FAR (check what is already answered) ---\n{conversation_context}\n\n"
            f"--- 6. RELEVANT NICE GUIDELINES (enrich risks/suggestions only, prefix with NICE:) ---\n{relevant_guidelines}\n"
        )

        llm = ChatOllama(
            model="llama3.2",
            temperature=0,
            num_predict=350,     # Tighter — live updates are concise
            num_thread=8,
            num_ctx=3000,
            repeat_penalty=1.15, # Discourage token repetition → faster convergence
            keep_alive=-1,       # Keep model in memory between calls (biggest speedup)
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
            gen_time = time.time() - gen_start
            print(f"[{consultation_id}] LIVE: Saved new live insight! (generated in {gen_time:.1f}s)")

        except json.JSONDecodeError:
            print(f"[{consultation_id}] LIVE: Failed to parse JSON. Raw:", response.content)

    except Exception as e:
        print(f"[{consultation_id}] LIVE: Error evaluating insights: {e}")
    finally:
        db.close()
        if consultation_id in PROCESSING_CONSULTATIONS:
            PROCESSING_CONSULTATIONS.remove(consultation_id)
