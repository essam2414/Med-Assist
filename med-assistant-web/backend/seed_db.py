import sys
from datetime import datetime, timedelta, timezone
import random

from app.db import SessionLocal
from app.models.user import User
from app.models.patient import Patient
from app.models.consultation import Consultation
from app.models.transcript import TranscriptEntry

db = SessionLocal()

# Find admin user or create one
admin_user = db.query(User).filter(User.email == "admin@example.com").first()
if not admin_user:
    from app.auth import get_password_hash
    admin_user = User(
        name="Admin User",
        email="admin@example.com",
        role="admin",
        hashed_password=get_password_hash("admin123")
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    print(f"Created admin user: {admin_user.email}")
else:
    print(f"Found existing admin user: {admin_user.email}")

# Delete existing mock data for admin
existing_patients = db.query(Patient).filter(Patient.doctor_id == admin_user.id).all()
for p in existing_patients:
    db.delete(p)
db.commit()

# Topic 1: Hypertension
transcript_htn = [
    ("doctor", "Good morning. How have you been feeling since our last visit?"),
    ("patient", "Good morning, Doctor. I've been doing alright mostly. Still getting used to the new medication."),
    ("doctor", "I see. Have you experienced any dizziness or headaches lately?"),
    ("patient", "A little bit of dizziness when I stand up too fast, but no headaches."),
    ("doctor", "That can be a side effect of the adjusted blood pressure medication. Are you taking it exactly as prescribed?"),
    ("patient", "Yes, every morning with my breakfast."),
    ("doctor", "Great. Let's go ahead and check your blood pressure now to see where we stand."),
    ("patient", "Okay, sounds good."),
    ("doctor", "Relax your arm here... just going to pump this up."),
    ("patient", "It always feels so tight."),
    ("doctor", "Almost done. Alright, it's reading at 135 over 85. That's actually a significant improvement from last time."),
    ("patient", "Oh, that's a relief. Last time it was in the 150s, right?"),
    ("doctor", "Exactly. The medication is definitely doing its job, but we'd still like it slightly lower over time. How has your diet been?"),
    ("patient", "I've been trying to cut back on salt. No more canned soups, and I stopped adding table salt to my meals."),
    ("doctor", "That's excellent to hear. Dietary changes play a huge role. What about exercise?"),
    ("patient", "I started walking for about thirty minutes every evening after dinner."),
    ("doctor", "Perfect. A brisk walk daily is fantastic for your cardiovascular health. Have you noticed any fatigue during those walks?"),
    ("patient", "Not really. Only if I try to push the pace too much, I get a little out of breath."),
    ("doctor", "That's completely normal. Just pace yourself. Now, regarding that dizziness upon standing... since your blood pressure is responding well, I don't want to lower the dose just yet. I recommend getting up slowly from a seated or lying position."),
    ("patient", "I can do that. If it gets worse, should I call your office?"),
    ("doctor", "Yes, absolutely. If you feel faint or the dizziness lasts more than a few moments, give us a call right away."),
    ("patient", "Okay, I will."),
    ("doctor", "I'd like to run a standard metabolic panel just to check your kidney function and electrolytes, as the medication can sometimes affect those levels."),
    ("patient", "Sure. Can I do the blood test today?"),
    ("doctor", "Yes, you can head down to the lab on the first floor right after we finish here. No fasting required for this one."),
    ("patient", "That's convenient."),
    ("doctor", "So, the plan is: continue the medication at the current dose, keep up the low-sodium diet and daily walks, and remember to stand up slowly. We'll review the lab results, and if anything is off, I'll contact you."),
    ("patient", "Sounds like a plan. When should I come back to see you?"),
    ("doctor", "Let's schedule a follow-up in three months time to check your progress again. Of course, reach out sooner if you have any concerns."),
    ("patient", "Thank you, Doctor. I'll get that scheduled at the front desk."),
    ("doctor", "You're welcome. Have a good rest of your day, and I'll see you in three months.")
]

# Topic 2: Asthma 
transcript_asthma = [
    ("doctor", "Hello there. I see you're in today because your asthma has been acting up. Tell me more about what's been going on."),
    ("patient", "Hi Doctor. Yes, over the last two weeks, I've been getting quite wheezy, especially at night."),
    ("doctor", "I'm sorry to hear that. How often are you waking up with shortness of breath or coughing?"),
    ("patient", "It's been about three or four times a week lately. It's really affecting my sleep."),
    ("doctor", "That's definitely concerning and indicates your asthma isn't well-controlled right now. Have you been using your rescue inhaler more frequently?"),
    ("patient", "Yes, I've had to use it almost every day. Sometimes twice a day."),
    ("doctor", "Okay. And what about your daily controller inhaler? Have you been taking that consistently?"),
    ("patient", "To be honest, I ran out about a month ago and kept forgetting to get a refill since I was feeling fine at the time."),
    ("doctor", "I see. That would explain the flare-up. The controller medication reduces the underlying inflammation in your airways. Without it, you become much more susceptible to triggers."),
    ("patient", "Yeah, I realize that now. Plus, the weather has been getting colder, and I think that's triggering it too."),
    ("doctor", "Cold air is a very common trigger. Have you had any signs of a respiratory infection? Like a fever, sore throat, or colored phlegm?"),
    ("patient", "No, none of that. Just the tight chest and wheezing."),
    ("doctor", "Alright. Let me have a listen to your lungs. Take a deep breath in... and out. Through your mouth, please."),
    ("patient", "[takes a deep breath]"),
    ("doctor", "And another one... Good. One more on the back here... Okay. There's definitely some expiratory wheezing bilaterally, which confirms the bronchospasm."),
    ("patient", "I could hear myself whistling earlier."),
    ("doctor", "Let's get you back on track. I'm going to send a prescription for your controller inhaler, Fluticasone, right now. You need to take two puffs twice a day, every single day, whether you feel symptoms or not."),
    ("patient", "Okay, I won't forget this time."),
    ("doctor", "Additionally, because you're having an acute flare-up, I'm going to prescribe a short five-day course of an oral steroid, Prednisone. This will hit the inflammation hard and quickly calm your airways down."),
    ("patient", "Will that make me jittery? I remember taking steroids once before and feeling very restless."),
    ("doctor", "It can, unfortunately. It might also increase your appetite and make it hard to sleep, which is why I recommend taking the whole daily dose in the morning with food."),
    ("patient", "Understood. Mornings with food."),
    ("doctor", "Exactly. And continue using your Albuterol rescue inhaler as needed for immediate relief, but if you find you're still needing it every day by the end of the week, I want you back here."),
    ("patient", "Okay, I will. But hopefully the new medication kicks in fast."),
    ("doctor", "It should. Do you use a spacer with your inhalers?"),
    ("patient", "No, I just spray it directly into my mouth."),
    ("doctor", "I highly recommend using a spacer. It ensures the medication actually gets into your lungs rather than hitting the back of your throat. I'll write a script for one of those as well."),
    ("patient", "Oh, okay. I'll try that out. How do you use it?"),
    ("doctor", "You attach the inhaler to the spacer, press the canister once, and then take a slow, deep breath in from the mouthpiece, holding it for ten seconds before exhaling."),
    ("patient", "That sounds simple enough."),
    ("doctor", "So, start the controller daily, take the five-day steroid course in the mornings, use the spacer, and keep the rescue inhaler on hand. Make a follow-up appointment for two weeks from now so we can reassess."),
    ("patient", "Sounds like a comprehensive plan. Thank you, Doctor."),
    ("doctor", "Anytime. Feel better, and don't hesitate to go to urgent care if you experience severe shortness of breath that the rescue inhaler doesn't fix.")
]

# Topic 3: Knee Pain
transcript_knee = [
    ("doctor", "Hi there. What brings you into the clinic today?"),
    ("patient", "Hello. I've been having some significant pain in my right knee for the past month or so."),
    ("doctor", "I'm sorry to hear that. Can you point to exactly where it hurts?"),
    ("patient", "It's mostly on the inside part of the knee, right around here."),
    ("doctor", "Okay, the medial aspect. Did you suffer any specific injury, like a twist, a fall, or a sports impact?"),
    ("patient", "No, nothing like that. It just sort of started gradually. At first it was an ache, but it's gotten sharper."),
    ("doctor", "When is the pain at its worst?"),
    ("patient", "Definitely when I go up or down stairs. Also, if I've been sitting for a long time, it's very stiff and hurts to stand up and take the first few steps."),
    ("doctor", "That stiffness after resting—does it usually improve after you've been moving for a few minutes?"),
    ("patient", "Yes, exactly. It loosens up after a bit, but then if I walk for too long, it starts aching again."),
    ("doctor", "Has the knee been swelling or locking up on you? Or giving way?" ),
    ("patient", "It swells occasionally by the end of the day, but it hasn't locked up or given way."),
    ("doctor", "Alright, let's take a look. Hop up on the examination table for me, please."),
    ("patient", "Okay."),
    ("doctor", "I'm going to manipulate your leg a bit. Let me know if anything causes sharp pain. Just relax your leg... There's a little bit of fluid buildup here. Does it hurt when I press on the joint line right here?"),
    ("patient", "Ouch, yes. Right there."),
    ("doctor", "Now I'm going to gently bend and straighten the knee... And let's test the ligaments. Pushing inward... pushing outward. Any pain there?"),
    ("patient", "No, that feels fine."),
    ("doctor", "Okay, the ligaments feel stable. And the meniscus test... turning the foot... does that cause a catch or pop?"),
    ("patient", "No catch, just a dull ache."),
    ("doctor", "Based on your symptoms and the exam, the medial joint line tenderness and the pain with stairs and stiffness after rest, this sounds a lot like early osteoarthritis of the knee."),
    ("patient", "Arthritis? But I'm not that old... am I?"),
    ("doctor", "Age is a factor, but wear and tear can happen to anyone over time. The cartilage that cushions the joint starts to thin out. It's very common."),
    ("patient", "Is there anything that can be done for it? Or do I just have to live with it?"),
    ("doctor", "There's a lot we can do to manage the symptoms and slow the progression. First, I'm going to order some X-rays of both knees while you're standing up. That will let us actually see the spacing between the bones and confirm the diagnosis."),
    ("patient", "Okay, X-rays sound like a good idea."),
    ("doctor", "In the meantime, I want you to manage the pain using Ibuprofen. Taking it with food will reduce stomach upset. It's an anti-inflammatory, so it will help with both the pain and the swelling."),
    ("patient", "Alright, I have some at home."),
    ("doctor", "Beyond medication, physical therapy is excellent for this. Strengthening the quadriceps muscles takes a lot of the load off the knee joint itself."),
    ("patient", "I can do physical therapy. Would a knee brace help?"),
    ("doctor", "An over-the-counter compression sleeve might offer some symptomatic relief and a feeling of support, but PT is the long-term solution."),
    ("patient", "Understood. Should I stop exercising? I usually do the treadmill."),
    ("doctor", "I don't want you to stop exercising, but I do suggest switching to lower-impact activities for a while. Try an exercise bike, swimming, or an elliptical machine instead of walking on an incline or running."),
    ("patient", "Okay, I'll switch to the bike at the gym."),
    ("doctor", "Let's get those X-rays done, start the Ibuprofen and physical therapy. Schedule a follow-up in four weeks to review the X-ray results and see how the knee is feeling with the interventions."),
    ("patient", "Great. Where do I get the X-ray?"),
    ("doctor", "They can do it right here in the imaging department down the hall. I'll put the order in now."),
    ("patient", "Thank you, Doctor. I really appreciate it.")
]

consultation_templates = [
    {"title": "Follow-up on Blood Pressure", "transcript": transcript_htn},
    {"title": "Asthma Checkup", "transcript": transcript_asthma},
    {"title": "Knee Pain Consultation", "transcript": transcript_knee}
]

patients_data = [
    {"name": "John Doe", "gender": "Male", "key_history": "Hypertension, Type 2 Diabetes"},
    {"name": "Jane Smith", "gender": "Female", "key_history": "Asthma, Migraines"},
    {"name": "Alice Johnson", "gender": "Female", "key_history": "Osteoarthritis, General wellness checkups"},
]

def generate_10_min_transcript(consultation_id, transcript_lines):
    entries = []
    current_time = 0.0
    
    # We want the total duration to be exactly 10 minutes (600 seconds)
    # The number of lines is len(transcript_lines), let's say roughly 30-34.
    # We need to distribute 600 seconds among these lines.
    # An average block per line would be 600 / len(transcript_lines) = ~18 seconds.
    
    target_duration = 600.0 
    average_duration_per_line = target_duration / len(transcript_lines)
    
    for speaker, text in transcript_lines:
        # Calculate speaking duration: roughly 2-3 words per second
        words = len(text.split())
        speaking_duration = (words / 2.5) + random.uniform(1.0, 2.0)
        
        # Calculate pause duration to pad out the time so it averages out correctly
        # We ensure pause isn't negative
        pause_duration = average_duration_per_line - speaking_duration
        if pause_duration < 1.0:
            # If the speaker spoke a really long time, reduce pause but keep it realistic
            pause_duration = random.uniform(1.0, 3.0)
            
        # Add some random jitter to make it imperfect / realistic
        jitter = random.uniform(-2.0, 2.0)
        pause_duration += jitter
        if pause_duration < 0.5:
            pause_duration = 0.5
            
        end_time = current_time + speaking_duration
        
        entries.append(TranscriptEntry(
            consultation_id=consultation_id,
            speaker=speaker,
            start_time=current_time,
            end_time=end_time,
            text=text
        ))
        
        current_time = end_time + pause_duration
        
    # the last entry doesn't need a pause, but the total time should now be very close to 600.
    
    return entries

for i, p_data in enumerate(patients_data):
    patient = Patient(
        doctor_id=admin_user.id,
        display_id=f"PT-{random.randint(1000, 9999)}",
        name=p_data["name"],
        date_of_birth=datetime(1970 + i * 5, 1, 1).date(),
        gender=p_data["gender"],
        key_history=p_data["key_history"]
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    
    # 2 consultations per patient
    for j in range(2):
        # Pick a topic that matches their history for realism, or random if 2nd visit
        topic = consultation_templates[i] if j == 0 else random.choice(consultation_templates)
        
        consultation = Consultation(
            doctor_id=admin_user.id,
            patient_id=patient.id,
            title=topic["title"],
            status="completed",
            created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30))
        )
        db.add(consultation)
        db.commit()
        db.refresh(consultation)
        
        transcript_entries = generate_10_min_transcript(consultation.id, topic["transcript"])
        # Actually set the consultation end time effectively
        last_entry = transcript_entries[-1]
        consultation.ended_at = consultation.created_at + timedelta(seconds=float(last_entry.end_time))
        
        db.bulk_save_objects(transcript_entries)
        db.commit()

print("Successfully seeded the database with coherent ~10-minute mock transcripts.")
