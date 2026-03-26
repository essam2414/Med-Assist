import json
import os
from pprint import pprint
# Ensure we map correctly to app dir
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db import SessionLocal
from app.models.ai_analytics import AIAnalytics
from app.models.consultation import Consultation
from app.models.insight import AIInsight
from app.models.patient import Patient
from app.models.user import User
from datetime import date

def main():
    db = SessionLocal()
    
    # Let's find the admin user. By default, admin might have 'admin' in email or role 'admin'.
    # In earlier logs, admin email was changed to essamsheikh24@gmail.com
    admin_user = db.query(User).filter(User.email == "essamsheikh24@gmail.com").first()
    if not admin_user:
        admin_user = db.query(User).filter(User.role == "admin").first()
        
    if not admin_user:
        # fallback to the first user with analytics
        analytics = db.query(AIAnalytics).all()
        if not analytics:
            print(json.dumps({"error": "No AI Analytics found in DB"}))
            return
        admin_id = analytics[0].doctor_id
    else:
        admin_id = admin_user.id

    analytics = db.query(AIAnalytics).filter(AIAnalytics.doctor_id == admin_id).all()
    
    output = []
    for a in analytics:
        c_details = a.consultation_details or []
        c_ids = [c['id'] for c in c_details]
        
        consultations = db.query(Consultation).filter(Consultation.id.in_(c_ids)).all()
        insights = db.query(AIInsight).filter(AIInsight.consultation_id.in_(c_ids)).all()
        
        c_data = []
        for c in consultations:
            p = db.query(Patient).filter(Patient.id == c.patient_id).first()
            ins = next((i for i in insights if i.consultation_id == c.id), None)
            c_data.append({
                "consultation_id": c.id,
                "title": c.title,
                "patient": p.name if p else "Anonymous",
                "insight_key_points": ins.key_points if ins else None,
                "about": c.about
            })
            
        output.append({
            "analytics_id": a.id,
            "week_start": str(a.week_start_date),
            "generated_summary": a.summary,
            "consultation_count": a.consultation_count,
            "patient_count": a.patient_count,
            "consultations": c_data
        })
        
    with open("analytics_dump.json", "w") as f:
        json.dump(output, f, indent=2)
        
    print(f"Dumped {len(output)} records to analytics_dump.json")

if __name__ == "__main__":
    main()
