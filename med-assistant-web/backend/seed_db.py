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
else:
    print(f"Found existing admin user: {admin_user.email}")

# Delete existing mock data for admin
existing_patients = db.query(Patient).filter(Patient.doctor_id == admin_user.id).all()
for p in existing_patients:
    db.delete(p)
db.commit()

# --- Dialogue Templates ---

# Patient 1: Hypertension History
c1_1 = [
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
    ("doctor", "Almost done. Alright, it's reading at 135 over 85. That's a significant improvement from last time."),
    ("patient", "Oh, that's a relief. Last time it was in the 150s, right?"),
    ("doctor", "Exactly. The medication is doing its job, but we'd still like it slightly lower over time. How has your diet been?"),
    ("patient", "I've been trying to cut back on salt. No more canned soups or table salt."),
    ("doctor", "That's excellent to hear. Let's run a standard metabolic panel just to check your kidney function and electrolytes."),
    ("patient", "Sure. Can I do the blood test today?"),
    ("doctor", "Yes, head down to the lab straight after. We will review the results soon.")
]

c1_2 = [
    ("doctor", "Hi there. I see you're coming in for some back pain today?"),
    ("patient", "Yes, my lower back has been killing me for the last four days."),
    ("doctor", "I'm sorry to hear that. Did you lift something heavy or twist it awkwardly?"),
    ("patient", "I was helping my friend move some furniture over the weekend. Afterwards, it just started tightening up."),
    ("doctor", "Is the pain staying in your lower back, or does it shoot down your legs?"),
    ("patient", "It's mostly just intense aching right in the center of my lower back. Doesn't go into my legs."),
    ("doctor", "Any numbness or tingling in your feet, or changes in your bowel or bladder habits?"),
    ("patient", "No, nothing like that. Just the muscle pain."),
    ("doctor", "That's good, it suggests it's primarily a muscular strain. Let's have you stand up and bend forward as far as you can."),
    ("patient", "Ouch, yeah, I can only go about halfway down before it pulls."),
    ("doctor", "Okay, take it easy. Lie down on the table here. I'm going to raise your straight leg... any pain there?"),
    ("patient", "Just a little tightness in the hamstring, but not the sharp back pain."),
    ("doctor", "Alright. Based on the exam, this is an acute lumbar sprain. I'd like you to use a heating pad, try some gentle stretching, and take Ibuprofen."),
    ("patient", "Okay, heat and Ibuprofen. Should I rest in bed?"),
    ("doctor", "Actually, prolonged bed rest is worse for it. Try to stay as active as you can tolerate without overdoing it."),
    ("patient", "Got it. How long will this take to heal?"),
    ("doctor", "Usually, these strains resolve in about a week or two. Let me know if it worsens.")
]

c1_3 = [
    ("doctor", "Hello. You mentioned you've been having trouble sleeping lately?"),
    ("patient", "Yes, for the past month, I just can't seem to fall asleep. My mind keeps racing."),
    ("doctor", "I'm sorry, that can be very exhausting. Are you under a lot of stress right now?"),
    ("patient", "Yes, work has been extremely demanding lately. We're launching a new project."),
    ("doctor", "Stress is a very common trigger for insomnia. How much caffeine are you drinking during the day?"),
    ("patient", "Probably three or four cups of coffee. I need it to stay awake since I'm not sleeping well."),
    ("doctor", "It's a difficult cycle. Caffeine stays in your system for hours and can make falling asleep even harder. I suggest cutting off caffeine by 2 PM."),
    ("patient", "That's going to be tough, but I can try. What about screen time before bed?"),
    ("doctor", "That's another big factor. The blue light from phones and laptops suppresses melatonin. Try to turn off all screens at least an hour before you want to sleep."),
    ("patient", "I usually read on my tablet in bed. Maybe I should switch to a paper book."),
    ("doctor", "A paper book with a warm reading light would be much better. Also, try to establish a relaxing wind-down routine."),
    ("patient", "Like taking a warm bath or listening to calm music?"),
    ("doctor", "Exactly. Let's try these sleep hygiene adjustments for two weeks. If you're still struggling, we can discuss short-term sleep aids."),
    ("patient", "Okay, I'll commit to the changes. I really just want a good night's rest.")
]

# Patient 2: Asthma
c2_1 = [
    ("doctor", "Hello there. I see you're in today because your asthma has been acting up?"),
    ("patient", "Hi Doctor. Yes, over the last two weeks, I've been getting quite wheezy, especially at night."),
    ("doctor", "How often are you waking up with shortness of breath or coughing?"),
    ("patient", "It's been about three or four times a week lately. It's really affecting my sleep."),
    ("doctor", "Have you been using your rescue inhaler more frequently?"),
    ("patient", "Yes, I've had to use it almost every day. Sometimes twice a day."),
    ("doctor", "And what about your daily controller inhaler? Have you been taking that consistently?"),
    ("patient", "To be honest, I ran out about a month ago and kept forgetting to get a refill."),
    ("doctor", "That would explain the flare-up. Let me listen to your lungs. Deep breath in and out..."),
    ("patient", "[takes a deep breath]"),
    ("doctor", "There's definitely some expiratory wheezing. I'm going to prescribe a short five-day course of Prednisone and get you back on your controller inhaler."),
    ("patient", "Okay, I'll make sure to pick up the refill today."),
    ("doctor", "Remember to take the steroid with food in the morning. And please use a spacer with your inhaler for better delivery."),
    ("patient", "Will do, thank you Doctor.")
]

c2_2 = [
    ("doctor", "Hi. You're here for a skin check today? You noticed a mole changing?"),
    ("patient", "Yes, there's a mole on my left shoulder that seems to have gotten darker and maybe a bit larger over the last few months."),
    ("doctor", "Let's definitely take a look. Can you point it out for me?"),
    ("patient", "Right here, just below the shoulder blade."),
    ("doctor", "Okay, I'm going to use my dermatoscope to get a magnified view of it. Hold still..."),
    ("patient", "Does it look concerning?"),
    ("doctor", "The borders are a little irregular, and there is some variation in the pigment. It's not definitively dangerous, but given the changes you've noticed, I'd like to do a punch biopsy to be safe."),
    ("patient", "A biopsy? Will that hurt?"),
    ("doctor", "I'll numb the area completely with a small injection of lidocaine first. You shouldn't feel anything other than a little pressure."),
    ("patient", "Okay, let's go ahead with it then."),
    ("doctor", "I'll get the tray set up. We'll send the sample to pathology, and it usually takes about a week to get results back."),
    ("patient", "Will it leave a scar?"),
    ("doctor", "It will leave a very small, round scar. I'll put a single stitch in it to help it heal nicely."),
    ("patient", "Okay, getting results in a week sounds fine.")
]

c2_3 = [
    ("doctor", "Welcome back. How have you been doing with the changing seasons?"),
    ("patient", "Terrible, actually. My allergies are worse than ever this spring."),
    ("doctor", "I'm sorry to hear that. What are your main symptoms right now?"),
    ("patient", "My nose is constantly runny and congested, my eyes water non-stop, and I've been sneezing all morning."),
    ("doctor", "Are you taking any over-the-counter antihistamines?"),
    ("patient", "I tried taking some standard Claritin, but it doesn't seem to touch it. Plus, it makes my mouth dry."),
    ("doctor", "Since the oral antihistamine isn't enough, we should try a steroid nasal spray like Flonase. It targets the inflammation directly in your nasal passages."),
    ("patient", "I haven't tried a nasal spray before. Do you use it every day?"),
    ("doctor", "Yes, and consistency is key. It takes a few days of daily use to see the full effect. One spray per nostril every morning."),
    ("patient", "I can do that. What about my eyes?"),
    ("doctor", "There are over-the-counter antihistamine eye drops, like Zaditor, that work very quickly for the itching and watering. Try those when your eyes flare up."),
    ("patient", "Great, I'll stop at the pharmacy. Oh, will the nasal spray affect my asthma?"),
    ("doctor", "No, it shouldn't negatively impact your asthma at all. In fact, controlling severe post-nasal drip can sometimes help asthma."),
    ("patient", "That's good to know. Thank you.")
]

# Patient 3: Osteoarthritis
c3_1 = [
    ("doctor", "Hi there. What brings you into the clinic today?"),
    ("patient", "Hello. I've been having some significant pain in my right knee for the past month or so."),
    ("doctor", "Can you point to exactly where it hurts?"),
    ("patient", "It's mostly on the inside part of the knee, right around here."),
    ("doctor", "When is the pain at its worst?"),
    ("patient", "Definitely when I go up or down stairs, or after I've been sitting for a long time."),
    ("doctor", "Let's take a look. I'm going to manipulate your leg a bit. Let me know if anything causes sharp pain... Does it hurt when I press on the joint line here?"),
    ("patient", "Ouch, yes. Right there."),
    ("doctor", "Based on your symptoms and the exam, this sounds a lot like early osteoarthritis of the knee. I'm going to order some X-rays to confirm."),
    ("patient", "Arthritis? Is there anything that can be done for it?"),
    ("doctor", "Yes, we can manage it. Start with Ibuprofen, and I want to refer you to physical therapy to strengthen the surrounding muscles."),
    ("patient", "Okay. How long is physical therapy?"),
    ("doctor", "Usually twice a week for about six weeks. We'll see how you progress.")
]

c3_2 = [
    ("doctor", "Hello. The nurse mentioned you're experiencing some pain when urinating?"),
    ("patient", "Yes, since yesterday morning, it's been burning a lot, and I feel like I have to go to the bathroom constantly."),
    ("doctor", "Any fever, chills, or back pain?"),
    ("patient", "No fever, but my lower stomach feels a bit achy and heavy."),
    ("doctor", "Okay. Based on those symptoms, it sounds very much like an uncomplicated Urinary Tract Infection (UTI). We'll test the urine sample you provided just now to confirm."),
    ("patient", "Will I need antibiotics?"),
    ("doctor", "Yes, let's get you started on a short course of antibiotics—Macrobid for five days. You should start feeling relief within 24 to 48 hours."),
    ("patient", "That would be wonderful. It's very uncomfortable."),
    ("doctor", "I'll also prescribe some Phenazopyridine. It's a medication that directly soothes the lining of your bladder to reduce the burning while the antibiotic kicks in. Just be warned, it will turn your urine bright orange."),
    ("patient", "Oh, good to know! I'll pick both of those up today."),
    ("doctor", "Drink plenty of water to help flush the bacteria out. If you develop a fever or severe back pain, go to the urgent care."),
    ("patient", "I will keep that in mind. Thank you.")
]

c3_3 = [
    ("doctor", "Good to see you for your annual physical. How have things been overall?"),
    ("patient", "Pretty good, Doctor. The knee physical therapy really helped, so I'm staying fairly active."),
    ("doctor", "That's fantastic. I see your weight is stable, and your vitals today look perfect. Have you noticed any changes in your appetite, energy levels, or mood?"),
    ("patient", "No, energy is good. I eat fairly well, try to stick to a Mediterranean diet."),
    ("doctor", "Excellent choice. We'll run the standard annual bloodwork—checking cholesterol, blood sugar, and liver and kidney function. I don't anticipate any issues given your healthy lifestyle."),
    ("patient", "Sounds reassuring."),
    ("doctor", "Since we are heading into October, it's also time for the seasonal flu shot. Are you okay getting that today?"),
    ("patient", "Yes, absolutely. Best to get it out of the way."),
    ("doctor", "Agreed. The nurse will be right in to administer the vaccine and draw your blood. Any other concerns before I let them in?"),
    ("patient", "I was wondering if I should be taking a calcium or vitamin D supplement for my bones?"),
    ("doctor", "We will check your Vitamin D level in the bloodwork today. If it's low, I'll recommend a dose. Otherwise, you likely get enough from your diet and sunlight."),
    ("patient", "Perfect, let's wait on the blood test then. Thanks for everything!")
]

# Patient 4: Type 2 Diabetes
c4_1 = [
    ("doctor", "Hello. We have your recent lab work back, including your HbA1c. Let's discuss."),
    ("patient", "I've been a bit worried about it. I admit I slipped up on my diet over the holidays."),
    ("doctor", "Your HbA1c is at 8.2% today. We'd ideally like to see it below 7%. It indicates your average blood sugar has been running high."),
    ("patient", "I knew it wouldn't be great. I've noticed I'm thirstier than usual too."),
    ("doctor", "The increased thirst is a direct symptom of high blood sugar. We need to tighten control to prevent long-term complications. I'd like to increase the dose of your Metformin."),
    ("patient", "Will the higher dose upset my stomach? Remember it did when I first started it."),
    ("doctor", "It might cause some mild GI upset initially. Taking it right in the middle of a large meal usually helps mitigate that significantly."),
    ("patient", "Okay, I'll make sure to take it with dinner."),
    ("doctor", "Alongside the medication adjustment, we really need to get back to the basics with your diet. Reducing refined carbohydrates and watching portion sizes."),
    ("patient", "I know, I need to stop snacking on bread and chips in the evening."),
    ("doctor", "Let's schedule a follow-up in three months to recheck the A1c and see how the new dose is working."),
    ("patient", "Sounds like a plan. I'll get back on track.")
]

c4_2 = [
    ("doctor", "Today is your comprehensive diabetic foot exam. Have you noticed any tingling, numbness, or pain in your feet?"),
    ("patient", "Sometimes at night, I get a slight tingling in my toes, but it usually goes away if I shake my feet out."),
    ("doctor", "Alright, take your shoes and socks off for me. I'm going to check the pulses in your feet first... good, circulation is strong on both sides."),
    ("patient", "That's good to hear. I try to walk every day to keep the blood flowing."),
    ("doctor", "Now I'm going to use this monofilament—it's like a stiff piece of plastic—to check your sensation. Close your eyes and tell me when you feel it poking your foot."),
    ("patient", "Okay."),
    ("doctor", "[pokes foot] Do you feel this?"),
    ("patient", "Yes."),
    ("doctor", "[pokes another spot] And this?"),
    ("patient", "Yes."),
    ("doctor", "[pokes heel] And here?"),
    ("patient", "I... think so? It's very faint."),
    ("doctor", "Okay. You have slightly diminished sensation on your heels, which aligns with the nighttime tingling. This is early peripheral neuropathy. It's crucial that you inspect your feet every single day for any cuts or blisters, since you might not feel them if they happen."),
    ("patient", "I will start checking them every night. Should I use a mirror?"),
    ("doctor", "Yes, a mirror makes it much easier to see the bottom of your feet. And make sure your shoes fit well and don't rub."),
    ("patient", "Got it. I'll be careful.")
]

c4_3 = [
    ("doctor", "We discussed last time that adjusting your diet would be a priority. How is that going?"),
    ("patient", "It's going okay, but I find myself confused at the grocery store. It's hard to know what's actually healthy versus just marketing."),
    ("doctor", "That's very common, nutrition labels can be tricky. Because you're highly motivated, I want to refer you to a registered dietician who specializes in diabetes management."),
    ("patient", "That sounds like exactly what I need. What will they do?"),
    ("doctor", "They will sit down with you, look at what you typically like to eat, and help you build a realistic meal plan. They focus on portion control, balancing macros, and reading those complicated labels."),
    ("patient", "Will my insurance cover it?"),
    ("doctor", "Most insurances cover diabetic education fully. The front desk will help ensure it's approved before your first visit."),
    ("patient", "Oh, excellent. I really struggle with finding good snacks that won't spike my sugar."),
    ("doctor", "The dietician will give you a big list of great options. In the meantime, try to pair carbohydrates with protein or fat—like having an apple with peanut butter, rather than just an apple by itself. It slows the sugar absorption."),
    ("patient", "That makes sense. Thank you, I'm looking forward to the referral.")
]

# Patient 5: Migraines
c5_1 = [
    ("doctor", "Good morning. You're here to discuss your migraines? Tell me how frequently you're getting them now."),
    ("patient", "Good morning. Yes, they've gotten much more frequent. I'm having about six to eight bad migraines a month now."),
    ("doctor", "That's definitely stepping into the chronic territory. Are they affecting your ability to work?"),
    ("patient", "Absolutely. I've had to call out sick twice this month because I couldn't look at a computer screen without throwing up."),
    ("doctor", "I'm sorry, that sounds debilitating. The sumatriptan we prescribed for when you get a migraine—is that still helping?"),
    ("patient", "It helps take the edge off if I take it immediately, but because I get them so often, I feel like I'm taking too much medication."),
    ("doctor", "You're right to be concerned about that; overuse can cause rebound headaches. Because you are having more than four migraine days a month, it's time to start a preventative medication rather than just treating them as they happen."),
    ("patient", "A preventative? Like something I take every day?"),
    ("doctor", "Exactly. I'd like to start you on Topiramate. It's taken daily and can significantly reduce the frequency and severity of your migraines over time."),
    ("patient", "Are there side effects?"),
    ("doctor", "Some people experience tingling in their fingers or toes, and it can sometimes cause a little cognitive haziness or word-finding difficulty. We'll start at a very low dose to minimize that."),
    ("patient", "I'm willing to try it if it means fewer migraines."),
    ("doctor", "Great. Start with 25mg at night for a week, then we'll slowly increase it. We'll reevaluate in one month.")
]

c5_2 = [
    ("doctor", "Hello. Let's talk about the stomach issues you've been having."),
    ("patient", "Hi Doctor. Yes, I've had this awful burning sensation in my chest, mostly after I eat dinner and lay down."),
    ("doctor", "Sounds like classic heartburn or acid reflux. Do you ever get a sour or bitter taste in the back of your throat?"),
    ("patient", "Yes, definitely. Sometimes it makes me cough a bit at night too."),
    ("doctor", "That nighttime cough is very typical of GERD—Gastroesophageal Reflux Disease. What time are you eating dinner?"),
    ("patient", "Usually quite late after I get home, around 8:00 PM. Then I might go to bed around 10:00 PM."),
    ("doctor", "Laying down that soon after eating allows the stomach acid to easily flow back up the esophagus. Try to have your last meal at least three hours before going to bed."),
    ("patient", "Three hours... okay, I'll need to adjust my schedule, maybe eat at work before leaving."),
    ("doctor", "That would be highly beneficial. I'm also going to prescribe Omeprazole, a proton-pump inhibitor. You'll take it once a day every morning, 30 minutes before breakfast."),
    ("patient", "Will this cure it?"),
    ("doctor", "It will drastically reduce the acid production so your esophagus can heal from the irritation. Try it for four weeks, keep adjusting your eating times, and avoid spicy foods and caffeine late in the day."),
    ("patient", "Understood. I'll get the prescription today.")
]

c5_3 = [
    ("doctor", "So, you are having some pain in your right shoulder? Let me take a look."),
    ("patient", "Yes, it aches constantly, but it gets really sharp when I try to lift my arm above my head, like putting a shirt on."),
    ("doctor", "Let's do a few range-of-motion tests. Slowly raise your arms out to the sides for me, like an airplane..."),
    ("patient", "Ouch... right there, about halfway up, it catches and hurts."),
    ("doctor", "Okay, you can put it down. Now tuck your elbow to your side and push outward against my hand..."),
    ("patient", "That hurts a bit too, deep inside the shoulder."),
    ("doctor", "That reproduces pain consistent with rotator cuff tendinitis or perhaps a tiny impingement. Has your job involved a lot of overhead lifting recently?"),
    ("patient", "Actually, I've been painting my entire house for the last two weekends. A lot of rolling the ceiling."),
    ("doctor", "That repetitive overhead motion is the classic culprit. The tendons get inflamed and pinched under the bone."),
    ("patient", "Do I need a Cortisone shot or surgery?"),
    ("doctor", "Not yet. You need to rest the shoulder for a few weeks—no overhead work. Ice it for 20 minutes twice a day, and I'll show you some pendulum exercises to keep the joint mobile without straining the tendon."),
    ("patient", "Okay, no more painting for a while. Will it heal on its own?"),
    ("doctor", "With rest and anti-inflammatories like Naproxen, it usually heals well. If it's not significantly better in three weeks, we will get an MRI and consider physical therapy or an injection."),
    ("patient", "Alright, I'll rest it and do the ice. Thank you.")
]

topics = [
    [("Follow-up on Blood Pressure", c1_1), ("Back Pain Evaluation", c1_2), ("Insomnia and Stress Management", c1_3)],
    [("Asthma Flare-up Checkup", c2_1), ("Routine Skin Mole Check", c2_2), ("Seasonal Allergies", c2_3)],
    [("Knee Pain Consultation", c3_1), ("Suspected UTI", c3_2), ("Annual Physical and Flu Shot", c3_3)],
    [("HbA1c Review", c4_1), ("Diabetic Foot Exam", c4_2), ("Dietician Referral", c4_3)],
    [("Chronic Migraine Consultation", c5_1), ("Acid Reflux Symptoms", c5_2), ("Right Shoulder Pain", c5_3)]
]

patients_meta = [
    {"name": "Arthur Pendelton", "gender": "Male", "key_history": "Hypertension, Occasional back pain"},
    {"name": "Beatrice Lowe", "gender": "Female", "key_history": "Asthma, History of atypical moles"},
    {"name": "Cedric Diggens", "gender": "Male", "key_history": "Osteoarthritis in knee, General wellness"},
    {"name": "Diana Rossing", "gender": "Female", "key_history": "Type 2 Diabetes, neuropathy concerns"},
    {"name": "Ethan Vance", "gender": "Male", "key_history": "Chronic Migraines, GERD"}
]

def generate_timed_transcript(consultation_id, transcript_lines):
    entries = []
    current_time = 0.0
    
    # Randomly target duration between 15 to 20 minutes (900 to 1200 seconds)
    target_duration = random.uniform(900.0, 1200.0) 
    average_duration_per_line = target_duration / len(transcript_lines)
    
    for speaker, text in transcript_lines:
        words = len(text.split())
        speaking_duration = (words / 2.5) + random.uniform(1.0, 2.0)
        
        pause_duration = average_duration_per_line - speaking_duration
        if pause_duration < 1.0:
            pause_duration = random.uniform(2.0, 4.0)
            
        jitter = random.uniform(-3.0, 3.0)
        pause_duration += jitter
        if pause_duration < 0.5:
            pause_duration = random.uniform(0.5, 2.0)
            
        end_time = current_time + speaking_duration
        
        entries.append(TranscriptEntry(
            consultation_id=consultation_id,
            speaker=speaker,
            start_time=current_time,
            end_time=end_time,
            text=text
        ))
        
        current_time = end_time + pause_duration
        
    return entries

for i, p_meta in enumerate(patients_meta):
    patient = Patient(
        doctor_id=admin_user.id,
        display_id=f"PT-{random.randint(1000, 9999)}",
        name=p_meta["name"],
        date_of_birth=datetime(1960 + i * 5, 1, 1).date(),
        gender=p_meta["gender"],
        key_history=p_meta["key_history"]
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    
    # 3 consultations per patient
    patient_topics = topics[i]
    for j in range(3):
        title, dialogue = patient_topics[j]
        consultation = Consultation(
            doctor_id=admin_user.id,
            patient_id=patient.id,
            title=title,
            status="completed",
            created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(1, 90))
        )
        db.add(consultation)
        db.commit()
        db.refresh(consultation)
        
        transcript_entries = generate_timed_transcript(consultation.id, dialogue)
        
        last_entry = transcript_entries[-1]
        consultation.ended_at = consultation.created_at + timedelta(seconds=float(last_entry.end_time))
        
        db.bulk_save_objects(transcript_entries)
        db.commit()

print("Successfully seeded the database with 5 patients, each having 3 distinct, realistic 15-20 min consultations.")
