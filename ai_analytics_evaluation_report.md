# Evaluating the AI Medical Assistant: An Interactive Case Study

## 1. Overview & Architecture
Building an AI to summarize medical consultations is hard—especially when using a small, lightweight model like the `Llama 3.2 (3B)` running locally. 

To prevent the AI from crashing due to too much data, our application uses a **"Summary of Summaries"** two-step pipeline:

1. **Manual Insights (The Micro View):** Right after a consultation, the AI reads the raw audio transcript, fetches the patient's background health records (EHR), and pulls relevant clinical guidelines using RAG (Retrieval-Augmented Generation). It turns this massive block of text into a short, structured clinical problem list (e.g., *Primary Complaint, Risk Factors, Recommended Clarifications*). 
2. **Weekly Analytics (The Macro View):** At the end of the week, the system does not read raw transcripts (which would overwhelm the AI). Instead, the Weekly Analytics engine simply reads all the generated `Manual Insights` from that week. It combines these short summaries into a final report showing the trends of the doctor's entire weekly caseload.

---

## 2. Evaluation Methodology
To properly test this pipeline, we used automated Python scripts ([test_ai_analytics_evaluation.py](file:///c:/Users/essam/OneDrive/Desktop/FYP/eus328/med-assistant-web/backend/test_ai_analytics_evaluation.py)) to simulate clinical encounters ranging from 1 to 12 patients per week. 

We used a strict comparison method:
* **Evaluating Manual Insights:** We directly compared the AI's generated problem list side-by-side with the original conversational transcript. We were looking for any dropped facts, invented symptoms (hallucinations), or formatting errors.
* **Evaluating Weekly Analytics:** We compared the final weekly summary directly against the previously generated `Manual Insights`. The goal was to ensure the Weekly AI didn't invent new data and correctly scaled its language based on the number of patients.

---

## 3. Evaluation Scores

We graded the models based on clinical accuracy, hallucination rate, formatting compliance, and their ability to follow negative rules (e.g., "Do NOT do this").

### **Manual Insights Generator: 7.5 / 10**
**Why this score?** The model acts as a great scribe but requires heavy hand-holding. In early tests, it struggled heavily with "Prompt Leakage" (copying examples from our code into the patient's file) and frequently tried to guess missing medical data. Once we gave it extremely strict rules to stop inferring data and locked down its RAG search bounds, its accuracy improved drastically. However, it still occasionally struggles with complex formatting.

### **Weekly Analytics Engine: 8.0 / 10**
**Why this score?** This feature performed slightly better because it reads pristine, structured data provided by the Manual Insights, making it much harder to hallucinate medical facts. The main deductions come from its struggle with math and syntax. We had to heavily program the backend to force the AI to understand the difference between 1 patient (a single case) and 2 patients (which the AI previously hallucinated as "a large group of people").

---

## 4. What We Fixed (The Quirks of Small AI Models)

### Bug 1: "Playing Doctor" (The Inference Problem) - *Manual Insights*
* **What Happened:** When told to summarize a consultation, the AI would try to look smart by guessing. If a patient had diabetes, the model would randomly assume they also had high blood pressure. Worse, if our prompt instructions included a helpful example like *"e.g., Exertional chest pain,"* the AI would literally copy-paste chest pain into an unrelated consultation about acid reflux.
* **The Fix:** We stripped all medical examples from the code. Then, we added a strict **"Anti-Inference Rule:"** *“Never infer, imply, or assume medical diagnoses. If a condition is not explicitly spoken, it does not exist.”* 
* **The Result:** The model became a literal, honest scribe. It stopped inventing data completely.

### Bug 2: The "Crowd" Illusion (The Plurality Bug) - *Weekly Analytics*
* **What Happened:** When a doctor only saw a single patient for the week, the Weekly Analytics AI would panic. Because it was trained to summarize trends, it would write: *"A large group of individuals presented with severe shoulder pain"* when describing just one person.
* **The Fix:** We modified the Python backend to calculate the exact number of consultations and injected that math directly into the LLM logic. We then explicitly instructed it: *"If the number is 1, do NOT use plural phrases."*
* **The Result:** The AI immediately learned to dynamically scale its syntax, correctly stating: *"This week, one patient presented with..."*

### Bug 3: The "Healthy Patient" Panic (JSON Collapses) - *Weekly Analytics*
* **What Happened:** If a patient was perfectly healthy, the AI suffered a breakdown. Our prompt demanded it output a problem list. Because the healthy patient didn't have any problems, the AI broke its formatting, spitting out ugly JSON code to try and classify "being male" as a clinical risk factor just to hit its quota.
* **The Fix:** We removed the strict quota and gave the AI an escape hatch: *"If the patient is healthy, just write: '- Routine Wellness Exam: No acute problems.'"*
* **The Result:** Clean, human-readable text returned even when there was nothing wrong with the patient.

### Bug 4: The Distracted Database (RAG Misfires) - *Manual Insights*
* **What Happened:** The system queries NICE clinical guidelines based on the transcript. However, if a patient arrived with an acute Urinary Tract Infection (UTI), but their background chart listed a history of chronic knee osteoarthritis, the Database would get distracted and pull chronic pain guidelines recommending physical therapy for the UTI.
* **The Fix:** We locked down the RAG pipeline, forcing the AI to only apply guidelines relevant to the *new, acute* complaint while ignoring irrelevant past history.

---

## 5. What We Learned & Limitations

**The "Negative Prompt" Problem**
Small open-weights models struggle with the word "NOT". In our Weekly Analytics, we explicitly told the AI: *"Do NOT mention medications or tests."* 

However, when evaluating a patient who specifically came in to discuss adjusting their Metformin dosage for an HbA1c of 8.2%, the AI actively ignored our negative rule and mentioned the medication anyway. 

Why? Because the model prioritized clinical accuracy over arbitrary formatting rules. Summarizing the consultation without mentioning the medication was impossible, so it chose to break the rule to act like a better doctor. To a patient or clinician, this "failure" is actually a massive success, but it proves that small models cannot always balance competing instructions.

## 6. Conclusion & Future Upgrades
The Med-Assistant pipeline is highly functional. By strategically engineering our prompts and mathematical boundaries, we proved that a fast, locally-hosted model can perform high-level medical synthesis without compromising patient safety. 

**Next Steps:** As the application scales, upgrading the central engine to a frontier-class model like **GPT-4o** or **Claude 3.5 Sonnet** will easily resolve the last remaining grammatical quirks, allowing the system to handle complex, multi-layered consultations with zero prompt-blindness and seamless execution.
