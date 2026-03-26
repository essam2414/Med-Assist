import os
import sys
import time
import json
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Prevent tokenizer warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Ensure we import from backend root
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.db import SessionLocal
from app.models.user import User
from app.models.patient import Patient
from app.models.consultation import Consultation
from app.models.transcript import TranscriptEntry
from app.models.live_insight import LiveInsight
from app.services.live_insight_service import evaluate_and_generate_live_insights

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

CRITIC_SYSTEM_PROMPT = """You are an expert Clinical AI Evaluator grading a real-time streaming medical extraction model.

The local AI generates four distinct JSON fields for every audio chunk. You must grade each field INDIVIDUALLY on a 0-10 scale based on clinical accuracy, adherence to the transcript, and adherence to the Known Patient context.

RULES FOR GRADING:
1. THE SPAM RULE: If the audio chunk is pure small-talk (e.g. weather, traffic), the AI MUST stay silent (which passes to you as 'NULL SILENCE'). If it outputs medical JSON for small talk, score ALL fields 0. If it correctly stayed silent, score ALL fields 10.
2. THE CORRECTION RULE: If the patient corrects themselves, the new output must reflect the newest truth.
3. THE HALLUCINATION RULE: Penalize hallucinated facts heavily. EXCEPTIONS: Do NOT penalize facts contained in the KNOWN PATIENT DATABASE CONTEXT, and do NOT penalize negative finding disclosures (e.g. 'no nausea mentioned') because the AI is programmed to output red-flag absences automatically.

EXPECTED FIELD LOGIC:
- summary_score: Must accurately capture the main complaint. Max 3 sentences.
- problems_score: Must group clinical facts into "Problem Level" statements (not atomic snippets like "Pain location: chest").
- suggestions_score: Must suggest next-logical questions that haven't already been addressed in the transcript.
- risks_score: Must explicitly capture risks, red-flag absences, and family history.

OUTPUT FORMAT:
Respond ONLY with a valid JSON object. No markdown fences.
{
  "summary_score": <int 0-10>,
  "problems_score": <int 0-10>,
  "suggestions_score": <int 0-10>,
  "risks_score": <int 0-10>,
  "overall_reasoning": "<1-3 sentences explaining the sub-scores.>"
}
"""

def evaluate_with_gpt4(cumulative_transcript, llm_output, patient_context):
    if not os.getenv("OPENAI_API_KEY"):
        return {"summary_score": "N/A", "problems_score": "N/A", "suggestions_score": "N/A", "risks_score": "N/A", "overall_reasoning": "Missing OpenAI Key"}

    evaluator = ChatOpenAI(model="gpt-4o", temperature=0)
    
    prompt = f"""--- KNOWN PATIENT DATABASE CONTEXT ---
{patient_context}

--- ENTIRE TRANSCRIPT RECORDED SO FAR ---
{cumulative_transcript}

--- LOCAL AI'S OUTPUT FOR THIS CURRENT CHUNK ---
{llm_output}
"""
    try:
        response = evaluator.invoke([
            SystemMessage(content=CRITIC_SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ])
        
        raw = response.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        
        return json.loads(raw)
    except Exception as e:
        return {"summary_score": 0, "problems_score": 0, "suggestions_score": 0, "risks_score": 0, "overall_reasoning": f"Critic Error: {e}"}

def run_live_eval():
    db = SessionLocal()
    
    admin = db.query(User).filter(User.role == "admin").first()
    if not admin:
        admin = db.query(User).first()
        
    patient = db.query(Patient).first()
    if not patient:
        print("Error: No patient found in DB.")
        db.close()
        return
        
    patient_context_str = f"Name: {patient.name}\nKey History: {patient.key_history}"
    
    print(f"\n=======================================================")
    print(f"       THOROUGH MULTI-SCENARIO LIVE INSIGHTS TEST      ")
    print(f"=======================================================")
    print(f"Loaded Patient Context: {patient.name} ({patient.key_history})")
    
    # Define 3 Distinct Medical Scenarios to test model rigidity
    scenarios = [
        {
            "id": "A_CARDIOLOGY",
            "name": "Scenario A: Exertional Chest Pain (Cardiology)",
            "chunks": [
                {"name": "Spam/Greeting", "speaker": "patient", "text": "Hello Doctor, the weather outside is absolutely beautiful today, I actually walked here instead of driving."},
                {"name": "Initial Symptom", "speaker": "patient", "text": "Well doctor, I've been having this really bad pain in my stomach. It started three days ago and it feels like a sharp burning."},
                {"name": "Correction", "speaker": "patient", "text": "Actually, let me correct myself. It's not in my stomach. It's definitely much higher up, right in the center of my chest. It only happens when I walk up stairs."},
                {"name": "Amnesia/Timeline", "speaker": "patient", "text": "Also I forgot to mention earlier, but I have been taking low dose aspirin every single morning for the past five years."}
            ]
        },
        {
            "id": "B_DERMATOLOGY",
            "name": "Scenario B: Suspicious Mole (Dermatology)",
            "chunks": [
                {"name": "Initial Symptom", "speaker": "patient", "text": "I'm here for my annual skin check. I noticed this dark mole on my back last week, it's been getting slowly larger and it's quite itchy."},
                {"name": "Fact Drop/Risks", "speaker": "patient", "text": "I should also mention my father sadly passed from melanoma when he was my age, so I'm a bit nervous about this spot."}
            ]
        },
        {
            "id": "C_PSYCHIATRY",
            "name": "Scenario C: Generalized Anxiety (Psychiatry)",
            "chunks": [
                {"name": "Initial Complaint", "speaker": "patient", "text": "I've just been feeling really overwhelmed lately, I can't sleep at all and I feel physically sick."},
                {"name": "Correction", "speaker": "patient", "text": "Actually, the sleeping isn't the problem, I just wake up at 3AM in a panic. And I have these random heart palpitations during the day."},
                {"name": "Unrelated Chatter", "speaker": "patient", "text": "My car broke down yesterday which was super annoying and cost me $500."}
            ]
        }
    ]
    
    results_data = []
    
    idx_counter = 0
    for scenario in scenarios:
        print(f"\n\n=======================================================")
        print(f"▶ STARTING {scenario['name']}")
        print(f"=======================================================")
        
        # Create unique mock consultation for each scenario
        c_id = None
        consult = Consultation(patient_id=patient.id, doctor_id=admin.id, title=f"Mock Test {scenario['id']}", status="draft")
        db.add(consult)
        db.commit()
        db.refresh(consult)
        c_id = consult.id
        
        start_time_counter = 0.0
        cumulative_transcript = ""
        
        for i, chunk in enumerate(scenario["chunks"]):
            print(f"\n[Chunk {i+1}: {chunk['name']}]")
            print(f"🎙️ \"{chunk['text']}\"")
            cumulative_transcript += f"[{chunk['speaker']}]: {chunk['text']}\n"
            
            t_entry = TranscriptEntry(consultation_id=c_id, speaker=chunk["speaker"], text=chunk["text"], start_time=start_time_counter, end_time=start_time_counter+5.0)
            db.add(t_entry)
            db.commit()
            start_time_counter += 5.0
            
            if i > 0:
                print("⏳ Waiting 13 seconds for backend throttle...")
                time.sleep(13)
                
            evaluate_and_generate_live_insights(c_id)
            latest_insight = db.query(LiveInsight).filter(LiveInsight.consultation_id == c_id).order_by(LiveInsight.created_at.desc()).first()
            
            llm_output_text = "NULL SILENCE (No Insight Generated)"
            if latest_insight:
                time_since_creation = (datetime.utcnow() - latest_insight.created_at).total_seconds()
                if time_since_creation < 10.0:
                    llm_output_text = (
                        f"SUMMARY: {latest_insight.summary}\n"
                        f"NEW PROBLEMS: {latest_insight.key_points}\n"
                        f"SUGGESTIONS: {latest_insight.suggested_questions}\n"
                        f"RISKS: {latest_insight.risk_flags}"
                    )
                    print(f"✅ Widget Updated!")
                else:
                    print(f"🔕 Skipped (Nothing materially new detected).")
            else:
                 print(f"🔕 Skipped (Null Output).")

            print("🧠 Grading 4 Sub-Fields...")
            grade = evaluate_with_gpt4(cumulative_transcript, llm_output_text, patient_context_str)
            
            print(f" 📊 Summary: {grade.get('summary_score', 0)}/10 | Problems: {grade.get('problems_score', 0)}/10 | Suggestions: {grade.get('suggestions_score', 0)}/10 | Risks: {grade.get('risks_score', 0)}/10")
            print(f" 📝 {grade.get('overall_reasoning', '')}")
            
            # Save to tabular list
            results_data.append({
                "Scenario": scenario['id'],
                "Test_Phase": chunk['name'],
                "Summary_Score": grade.get('summary_score', 0),
                "Problems_Score": grade.get('problems_score', 0),
                "Suggestions_Score": grade.get('suggestions_score', 0),
                "Risks_Score": grade.get('risks_score', 0),
                "Reasoning": grade.get('overall_reasoning', '')
            })
            
        # Cleanup scenario
        db.query(LiveInsight).filter(LiveInsight.consultation_id == c_id).delete()
        db.query(TranscriptEntry).filter(TranscriptEntry.consultation_id == c_id).delete()
        db.query(Consultation).filter(Consultation.id == c_id).delete()
        db.commit()
        
    db.close()
    
    print("\n\n=======================================================")
    print("✅ Testing Complete. Saving Results CSV...")
    df = pd.DataFrame(results_data)
    
    # Calculate Averages Robustly (Ignoring any errors/strings)
    avg_sum = pd.to_numeric(df['Summary_Score'], errors='coerce').mean()
    avg_prob = pd.to_numeric(df['Problems_Score'], errors='coerce').mean()
    avg_sugg = pd.to_numeric(df['Suggestions_Score'], errors='coerce').mean()
    avg_risk = pd.to_numeric(df['Risks_Score'], errors='coerce').mean()
    
    print(f"\n=======================================================")
    print(f"                 FINAL EVALUATION SCORES               ")
    print(f"=======================================================")
    print(f" 📝 Summary Accuracy:        {avg_sum:.2f} / 10")
    print(f" 🩺 Problem Extraction:      {avg_prob:.2f} / 10")
    print(f" 💡 Suggested Questions:     {avg_sugg:.2f} / 10")
    print(f" ⚠️ Risks/Context Tracking:  {avg_risk:.2f} / 10")
    print(f"=======================================================\n")
    
    df.to_csv("live_insights_thorough_evaluation.csv", index=False)
    print("Detailed tabular data saved to 'live_insights_thorough_evaluation.csv'")

if __name__ == "__main__":
    run_live_eval()
