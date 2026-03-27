# Evaluating the AI Analytics Feature

## 1. Overview & Architecture
Building an AI to summarize medical consultations using a small, lightweight `Llama 3.2 (3B)` running locally. 

To prevent the AI from crashing due to too much data, the application uses a two-step pipeline:

1. **Manual Insights (The Micro View):** Right after a consultation, the AI reads the raw audio transcript, fetches the patient's background information, and pulls relevant clinical guidelines using RAG. It turns this massive block of text into a short, structured clinical problem list (e.g., *Primary Complaint, Risk Factors, Recommended Clarifications*). 
2. **Weekly Analytics (The Macro View):** For the weekly summaries, the system does not read raw transcripts (which would overwhelm the AI). Instead, the Weekly Analytics engine simply reads all the generated `Manual Insights` from that week. It combines these short summaries into a final report showing the trends of the doctor's entire week.

---

## 2. Evaluation Methodology
To properly test this pipeline, I used automated Python scripts ([test_ai_analytics_evaluation.py](file:///c:/Users/essam/OneDrive/Desktop/FYP/eus328/med-assistant-web/backend/test_ai_analytics_evaluation.py)) to simulate clinical encounters ranging from 1 to 12 patients per week. 

A strict comparison method was used:
* **Evaluating Manual Insights:** I directly compared the AI's generated problem list with the original transcript. I looked for any dropped facts, invented symptoms (hallucinations), or formatting errors.
* **Evaluating Weekly Analytics:** I compared the final weekly summary directly against the previously generated `Manual Insights`. The goal was to ensure the AI analytics didn't invent new data and correctly scaled its language based on the number of patients.

---

## 3. Evaluation Scores

I graded the model based on clinical accuracy, hallucination rate, formatting compliance, and its ability to follow negative rules (e.g., "Do NOT do this").

### **Manual Insights Generator: 7.5 / 10**
**Why this score?** The model was good at summarising but required a lot of guidance. In early tests, it struggled heavily with "Prompt Leakage" (copying examples from the code into the patient's file) and frequently tried to guess missing medical data. I then gave it strict rules to stop inferring data and locked down its RAG search bounds, its accuracy improved greatly. However, it still occasionally struggles with complex formatting.

### **Weekly Analytics Engine: 8.0 / 10**
**Why this score?** This feature performed slightly better because it reads structured data provided by the Manual Insights, making it much harder to hallucinate medical facts. The main problems come from its struggle with math and syntax. I had to program the backend to force the AI to understand the difference between 1 patient (a single case) and 2 patients (which the AI previously hallucinated as "a large group of people").

---

## 4. What Was Fixed (The Quirks of Small AI Models)

### Bug 1: "Playing Doctor" (The Inference Problem) - *Manual Insights*
* **What Happened:** When told to summarize a consultation, the AI would try by guessing. If a patient had diabetes, the model would randomly assume they also had high blood pressure. if prompt instructions included a helpful example like *"e.g., Exertional chest pain,"* the AI would copy-paste chest pain into an unrelated consultation about acid reflux.
* **The Fix:** I stripped all medical examples from the code. Then, added a strict **"Anti-Inference Rule:"** *“Never infer, imply, or assume medical diagnoses. If a condition is not explicitly spoken, it does not exist.”* 
* **The Result:** The model became a literal, honest scribe. It stopped inventing data completely.

### Bug 2: The "Crowd" Illusion (The Plurality Bug) - *Weekly Analytics*
* **What Happened:** When a doctor only saw a single patient for the week, the Weekly Analytics AI would hallucinate. Because it was trained to summarize large trends, it would write: *"A large group of individuals presented with severe shoulder pain"* when describing just one person.
* **The Fix:** I modified the Python backend to calculate the exact number of consultations and injected that math directly into the LLM logic. I then explicitly instructed it: *"If the number is 1, do NOT use plural phrases."*
* **The Result:** The AI immediately learned to dynamically scale its syntax, correctly stating: *"This week, one patient presented with..."*

### Bug 3: The "Healthy Patient" Panic (JSON Collapses) - *Weekly Analytics*
* **What Happened:** If a patient was perfectly healthy, the AI hallucinated. The prompt demanded it output a problem list. Because the healthy patient didn't have any problems, the AI broke its formatting, spitting out JSON code to try and classify "being male" as a clinical risk factor.
* **The Fix:** I removed the strict quota and gave the AI these instructions: *"If the patient is healthy, just write: '- Routine Wellness Exam: No acute problems.'"*
* **The Result:** Clean, human-readable text returned even when there was nothing wrong with the patient.

### Bug 4: The Distracted Database (RAG Misfires) - *Manual Insights*
* **What Happened:** The system queries NICE clinical guidelines based on the transcript. However, if a patient arrived with an acute Urinary Tract Infection (UTI), but their background chart listed a history of chronic knee osteoarthritis, the Database would get distracted and pull chronic pain guidelines recommending physical therapy for the UTI.
* **The Fix:** I locked the RAG pipeline, forcing the AI to only apply guidelines relevant to the *new, acute* complaint while ignoring irrelevant past history.

---

## 5. What I Learned & Limitations

**The "Negative Prompt" Problem**
Small open-weights models struggle with the word "NOT". In the Weekly Analytics, I explicitly told the AI: *"Do NOT mention medications or tests."* 

However, when evaluating a patient who specifically came in to discuss adjusting their Metformin dosage for an HbA1c of 8.2%, the AI actively ignored our negative rule and mentioned the medication anyway. 

Why? Because the model prioritized clinical accuracy over arbitrary formatting rules. Summarizing the consultation without mentioning the medication was impossible, so it chose to break the rule to act like a better doctor. To a patient or clinician, this can be seen as a benefit, but it proves that small models cannot always balance competing instructions.

## 6. Conclusion & Future Upgrades
The Med-Assistant pipeline is functional. By engineering the prompts and maths boundaries, I made a fast, locally-hosted model that can perform high-level medical synthesis without compromising patient safety. 

**Next Steps:** As the application scales, upgrading the model to a more powerful model like **GPT-4o** or **Claude 3.5 Sonnet** will easily resolve the last remaining grammatical issues, allowing the system to handle complex, multi-layered consultations with zero prompt-blindness and seamless execution.
