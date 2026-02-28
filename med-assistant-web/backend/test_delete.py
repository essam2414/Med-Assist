import sys
sys.path.append('c:/Users/essam/OneDrive/Desktop/FYP/eus328/med-assistant-web/backend')
from app.db import SessionLocal
from app.models.patient import Patient
from app.models.consultation import Consultation
from app.models.transcript import TranscriptEntry
from app.models.insight import AIInsight

db = SessionLocal()
p = db.query(Patient).first()
if p:
    print(f"Deleting patient {p.id}")
    cons = db.query(Consultation).filter(Consultation.patient_id == p.id).all()
    for c in cons:
        print(f"Deleting consultation {c.id}")
        db.query(TranscriptEntry).filter(TranscriptEntry.consultation_id == c.id).delete()
        db.query(AIInsight).filter(AIInsight.consultation_id == c.id).delete()
        db.delete(c)
    
    db.delete(p)
    try:
        db.commit()
        print("Success!")
    except Exception as e:
        print(f"Error: {e}")
else:
    print("No patients found")
