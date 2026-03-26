import asyncio
import time
from datetime import date
from app.db import SessionLocal
from app.models.user import User
from app.models.consultation import Consultation
from app.models.patient import Patient
from app.models.insight import AIInsight
from app.services.ai_analytics_service import generate_weekly_analytics

async def evaluate_analytics_12_cases():
    print("==================================================")
    print("🔥  AI ANALYTICS - 12 CASE STRESS TEST  🔥")
    print("==================================================\n")
    
    db = SessionLocal()
    dummy_doctor = None
    patient_ids = []
    consultation_ids = []
    
    try:
        # --- 1. SETUP DUMMY DATA ---
        print("[1] Setting up mock data for 12 consultations...")
        
        dummy_doctor = User(
            name="Dr. Maximum Stress",
            email="dr.maxstress@test.com",
            hashed_password="mock",
            role="doctor"
        )
        db.add(dummy_doctor)
        db.commit()
        db.refresh(dummy_doctor)

        # Target week for evaluation
        eval_date = date(2022, 10, 5) 

        # Patient Names and Health Issues (12 Distinct cases)
        mock_cases = [
            ("Alice Anderson", "Asthma Followup", "Patient experiencing mild shortness of breath and wheezing at night. Exacerbated by cold weather."),
            ("Bob Burno", "Chest Pain", "Patient complains of sharp, recurrent chest pain radiating to the left arm. Pain lasts for 5-10 minutes."),
            ("Carla Chavez", "Diabetes Review", "Type 2 Diabetes. Patient reports excessive thirst and frequent urination. Fasting blood sugar elevated."),
            ("David Dune", "Migraine", "Severe, throbbing headaches unilateral to the right side accompanied by photophobia and nausea."),
            ("Evelyn Ellis", "Back Pain", "Chronic lower back pain localized to L4-L5 region. Worsens with prolonged standing. No sciatica."),
            ("Frank Finn", "Hypertension", "Routine checkup for hypertension. Patient admits to poor diet and lack of exercise. BP currently 150/95."),
            ("Gina Gomez", "Acid Reflux", "Experiencing severe heartburn post-meals, especially after spicy food. Relieved partially by antacids."),
            ("Harry Hale", "Insomnia", "Trouble falling asleep and staying asleep. Averages 3 hours per night due to severe work-related stress anxiety."),
            ("Ivy Ireland", "Knee Pain", "Right knee osteoarthritis. Swelling and stiffness in the morning. Limited range of motion due to pain."),
            ("Jack Jones", "Skin Rash", "Pruritic erythematous rash on bilateral forearms. Started 2 days ago after exposure to a new laundry detergent."),
            ("Katie Kwan", "Depression Screen", "Patient reports low mood, anhedonia, and severe fatigue lasting over a month. PHQ-9 score highly elevated."),
            ("Liam Luo", "Ear Infection", "Right ear pain and muffled hearing. Otoscopy reveals bulging, erythematous tympanic membrane.")
        ]
        
        # Insert 12 Patients & 12 Consultations & 12 Insights
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
        print(f"    Injected 12 mock consultations into week of {eval_date}...\n")
        
        # --- 2. EVALUATE LLM PERFORMANCE ---
        print("[2] Triggering LLM Generation (llama3.2 ChatOllama)...")
        print("    Measuring latency with 12 distinct contextual cases mapped together...\n")
        
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
        print(f"[ ] Exact Duration Required: {duration:.2f} seconds.")
        print(f"[ ] Did the LLM run out of 'num_ctx' tokens, or ignore half the cases? Review the paragraph above to see if it missed anything like 'ear infection' or 'rash'.")

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
    asyncio.run(evaluate_analytics_12_cases())
