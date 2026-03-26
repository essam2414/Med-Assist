import asyncio
import time
from datetime import date
from app.db import SessionLocal
from app.models.user import User
from app.models.consultation import Consultation
from app.models.patient import Patient
from app.models.insight import AIInsight
from app.services.ai_analytics_service import generate_weekly_analytics

async def evaluate_analytics_6_cases():
    print("==================================================")
    print("🧪  AI ANALYTICS - 6 CASE STRESS TEST  🧪")
    print("==================================================\n")
    
    db = SessionLocal()
    dummy_doctor = None
    patient_ids = []
    consultation_ids = []
    
    try:
        # --- 1. SETUP DUMMY DATA ---
        print("[1] Setting up mock data for 6 consultations...")
        
        dummy_doctor = User(
            name="Dr. Stress Tester",
            email="dr.stresstest@test.com",
            hashed_password="mock",
            role="doctor"
        )
        db.add(dummy_doctor)
        db.commit()
        db.refresh(dummy_doctor)

        # Target week for evaluation
        eval_date = date(2021, 5, 20) 

        # Patient Names and Health Issues
        mock_cases = [
            ("Alice Anderson", "Asthma Followup", "Patient experiencing mild shortness of breath and wheezing at night. Exacerbated by cold weather."),
            ("Bob Burno", "Chest Pain", "Patient complains of sharp, recurrent chest pain radiating to the left arm. Pain lasts for 5-10 minutes."),
            ("Carla Chavez", "Diabetes Review", "Type 2 Diabetes. Patient reports excessive thirst and frequent urination. Fasting blood sugar elevated."),
            ("David Dune", "Migraine", "Severe, throbbing headaches unilateral to the right side accompanied by photophobia and nausea."),
            ("Evelyn Ellis", "Back Pain", "Chronic lower back pain localized to L4-L5 region. Worsens with prolonged standing. No sciatica."),
            ("Frank Finn", "Hypertension", "Routine checkup for hypertension. Patient admits to poor diet and lack of exercise. BP currently 150/95.")
        ]
        
        # Insert 6 Patients & 6 Consultations & 6 Insights
        for name, title, issue in mock_cases:
            p = Patient(doctor_id=dummy_doctor.id, name=name)
            db.add(p)
            db.commit()
            db.refresh(p)
            patient_ids.append(p.id)
            
            c = Consultation(doctor_id=dummy_doctor.id, patient_id=p.id, title=title, status="completed")
            c.created_at = eval_date
            db.add(c)
            db.commit()
            db.refresh(c)
            consultation_ids.append(c.id)
            
            ins = AIInsight(consultation_id=c.id, key_points=issue)
            db.add(ins)
            db.commit()

        print(f"✅  Mock data created! (Doctor ID: {dummy_doctor.id})")
        print(f"    Injected 6 mock consultations into week of {eval_date}...\n")
        
        # --- 2. EVALUATE LLM PERFORMANCE ---
        print("[2] Triggering LLM Generation (llama3.2 ChatOllama)...")
        print("    Measuring latency with increased context size...\n")
        
        start_time = time.time()
        
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
        
        print("\n🔎  Stress-Test Observations:")
        print(f"[ ] Did generation take significantly longer than ~6 seconds? (Took {duration:.2f}s)")
        print(f"[ ] Did the LLM successfully compress 6 unique problems into a readable paragraph?")

    except Exception as e:
        print(f"\n❌ Error during evaluation: {e}")
        
    finally:
        # --- 4. CLEANUP DUMMY DATA ---
        print("\n[3] Cleaning up database...")
        try:
            if dummy_doctor:
                db.query(AIInsight).filter(AIInsight.consultation_id.in_(consultation_ids)).delete(synchronize_session=False)
                db.query(Consultation).filter(Consultation.doctor_id == dummy_doctor.id).delete(synchronize_session=False)
                db.query(Patient).filter(Patient.doctor_id == dummy_doctor.id).delete(synchronize_session=False)
                db.query(User).filter(User.id == dummy_doctor.id).delete(synchronize_session=False)
                db.commit()
                print("✅  Cleanup successful.")
        except Exception as cleanup_err:
            print(f"⚠️  Cleanup partially failed: {cleanup_err}")
            
        db.close()

if __name__ == "__main__":
    asyncio.run(evaluate_analytics_6_cases())
