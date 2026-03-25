import asyncio
import time
from datetime import date, timedelta
from app.db import SessionLocal
from app.models.user import User
from app.models.consultation import Consultation
from app.models.patient import Patient
from app.models.insight import AIInsight
from app.services.ai_analytics_service import generate_weekly_analytics

async def evaluate_analytics():
    print("==================================================")
    print("🧪  AI ANALYTICS - LLM EVALUATION SCRIPT  🧪")
    print("==================================================\n")
    
    db = SessionLocal()
    try:
        # --- 1. SETUP DUMMY DATA ---
        print("[1] Setting up mock data for testing...")
        
        # Create a temporary evaluator doctor
        dummy_doctor = User(
            name="Dr. Evaluator",
            email="dr.evaluator@test.com",
            hashed_password="mock",
            role="doctor"
        )
        db.add(dummy_doctor)
        db.commit()
        db.refresh(dummy_doctor)

        # Create dummy patients
        p1 = Patient(doctor_id=dummy_doctor.id, name="Alice Anderson")
        p2 = Patient(doctor_id=dummy_doctor.id, name="Bob Burno")
        db.add_all([p1, p2])
        db.commit()
        db.refresh(p1)
        db.refresh(p2)

        # Target week for our evaluation (let's use a week far in the past to avoid collisions)
        eval_date = date(2020, 1, 15) # middle of a week
        
        # Create completed consultations for that week
        c1 = Consultation(doctor_id=dummy_doctor.id, patient_id=p1.id, title="Asthma Followup", status="completed")
        c2 = Consultation(doctor_id=dummy_doctor.id, patient_id=p2.id, title="Chest Pain", status="completed")
        c1.created_at = eval_date
        c2.created_at = eval_date
        db.add_all([c1, c2])
        db.commit()
        db.refresh(c1)
        db.refresh(c2)

        # Inject fake API Insights (this is what the Analytics LLM actually reads)
        ins1 = AIInsight(
            consultation_id=c1.id, 
            key_points="Patient experiencing mild shortness of breath and wheezing at night. Exacerbated by cold weather. Currently on Albuterol."
        )
        ins2 = AIInsight(
            consultation_id=c2.id, 
            key_points="Patient complains of sharp, recurrent chest pain radiating to the left arm. Pain lasts for 5-10 minutes. Relieved slightly by rest."
        )
        db.add_all([ins1, ins2])
        db.commit()

        print(f"✅  Mock data created! (Doctor ID: {dummy_doctor.id})")
        print(f"    Injected 2 mock consultations into week of {eval_date}")
        print("    - Case 1: Asthma / Shortness of breath")
        print("    - Case 2: Chest pain radiating to left arm\n")
        
        # --- 2. EVALUATE LLM PERFORMANCE ---
        print("[2] Triggering LLM Generation (llama3.2 ChatOllama)...")
        print("    Measuring latency and evaluating output quality...\n")
        
        start_time = time.time()
        
        # Run the weekly analytics function
        result = await generate_weekly_analytics(
            db=db, 
            doctor_id=dummy_doctor.id, 
            doctor_name=dummy_doctor.name, 
            target_date=eval_date, 
            generate_summary=True
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # --- 3. PRINT RESULTS ---
        print("==================================================")
        print("📊  EVALUATION RESULTS  📊")
        print("==================================================")
        print(f"⏱️  Time to Generate: {duration:.2f} seconds")
        print(f"👥  Patients Processed: {result.patient_count}")
        print(f"📋  Consultations Found: {result.consultation_count}\n")
        
        print("🧠  LLM GENERATED SUMMARY:")
        print("-" * 50)
        print(result.summary)
        print("-" * 50)
        
        # Evaluation Checks
        print("\n🔎  Self-Evaluation Checklist:")
        print(f"[ ] Did it take less than 10 seconds? (Took {duration:.2f}s)")
        print(f"[ ] Did it successfully synthesize BOTH 'asthma/wheezing' and 'chest pain'? Check the text above.")
        print(f"[ ] Did it hallucinate medical advice/diagnoses? (It should ONLY state what was discussed).")

    except Exception as e:
        print(f"\n❌ Error during evaluation: {e}")
        
    finally:
        # --- 4. CLEANUP DUMMY DATA ---
        print("\n[3] Cleaning up database...")
        try:
            db.query(AIInsight).filter(AIInsight.consultation_id.in_([c1.id, c2.id])).delete(synchronize_session=False)
            db.query(Consultation).filter(Consultation.doctor_id == dummy_doctor.id).delete(synchronize_session=False)
            db.query(Patient).filter(Patient.doctor_id == dummy_doctor.id).delete(synchronize_session=False)
            db.query(User).filter(User.id == dummy_doctor.id).delete(synchronize_session=False)
            db.commit()
            print("✅  Cleanup successful.")
        except Exception as cleanup_err:
            print(f"⚠️  Cleanup partially failed: {cleanup_err}")
            
        db.close()

if __name__ == "__main__":
    asyncio.run(evaluate_analytics())
