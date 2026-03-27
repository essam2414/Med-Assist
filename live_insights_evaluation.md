# Evaluating the "Live Insights" Feature

## 1. How the Pipeline Works
Evaluating a real-time AI feature is different from grading a standard chat prompt because the context never stops changing. 

To make the UI update instantly during a live doctor's appointment, I bypassed the heavy RAG database. Instead, my backend utilizes a quick processing system. Every 12 seconds, a background worker pulls the newest spoken sentences, pairs them with a compressed list of "Established Facts", and feeds them into the local `Llama 3.2 (3B)` model. The AI then pushes a JSON widget to the doctor's screen highlighting new problems, tracking risks, and suggesting next logical questions.

## 2. Testing Methodology
Because Live Insights keep changing and overwriting themselves, I couldn't use standard grading tools. Instead I used two strategies to evaluate the feature:

### Manual Real-Time Testing
Before writing any automated scripts, I had to ensure the WebSockets and AI triggers actually worked in a live environment. I manually enacted several mock medical consultations using the Vexa transcription bot inside Google Meet. By acting out different clinical scenarios live, I visually verified that the UI widgets spawned at the correct latencies and checked whether the extracted facts loosely made sense over a 7-minute conversation.

### Automated GPT-4o Critic
To get an unbiased, mathematical grade on the AI's clinical accuracy, I built a custom Python testing suite. I mocked three diverse scenarios (Cardiology, Dermatology, and Psychiatry) and fed audio chunks to `Llama 3.2` designed to trigger specific mechanics:
* **The Spam Test:** Feeding it small talk to ensure it stays silent.
* **The Correction Test:** Having the patient overwrite a symptom (e.g., stomach pain to chest pain).
* **The Amnesia Test:** Supplying an unrelated fact to ensure the model connects it to earlier symptoms without hallucinating.

After every chunk, my script sent the local AI's output to a GPT-4o Critic Agent, which strictly graded four sub-fields out of 10 based on the raw transcript and the patient's existing database history.

## 3. Engineering Progress & The Grades
During initial testing, the automated evaluation scores were bad. The model regularly failed to extract key facts, hallucinated context, and struggled to break the 3/10 barrier. However, through aggressive optimization, I pushed the final baseline averages to **~7.5 / 10**:

* **Summary Accuracy:** ~7.78 / 10
* **Problem Extraction:** ~6.78 / 10
* **Suggested Questions:** ~8.33 / 10
* **Risks & Context Tracking:** ~7.22 / 10

Here is exactly what I had to fix to raise the grades:

### The 120-Character Bug
The biggest jump in scores came from finding a hidden flaw. Originally, my backend blocked any audio chunk shorter than 120 characters to save CPU cycles. This was blinding the AI to important medical facts. During testing, a 116-character sentence revealing a family history of melanoma was completely blocked, resulting in 0/10 scores from the Critic. I removed the character limit, relying exclusively on my 12-second time-throttle. The AI instantly caught the melanoma fact on the next run, jumping to a perfect 10/10 for Risk Tracking.

### Prompt Consolidation
Early versions of my `SYSTEM_PROMPT` confused the small `Llama 3.2` model. I restricted the prompt by forcing the LLM to output rigid JSON formatting and automatically compress "Established Facts" into single bullets to prevent the AI from repeatedly drowning in old text. 

## 4. Model Limitations
While the streaming pipeline is good, running a tiny 3-Billion parameter model locally revealed a hard ceiling for clinical reasoning.

### The "Eager Summarizer" (Spam Rule Failure)
Smaller models struggle with Negative Constraints. When instructed to stay silent if the transcript only contains small talk, `Llama 3.2` didn't always comply. When the mock patient complained about their car breaking down, the AI ignored the silence rule and documented "Car trouble causing annoyance" as a clinical medical problem, giving it a worse score.

### "Ghost Memory" 
The AI successfully caught initial symptoms, but struggled to process human corrections. When the patient corrected their "stomach pain" to "chest pain," the AI added the chest pain correctly, but struggled to permanently delete "stomach pain" from its internal JSON cache. 

### Conclusion
The evaluation proves the model successfully manages live streaming states and latencies. To push this system to a production-ready `9.5/10`, the architecture itself doesn't need to change; the backend simply needs to map to a more powerful LLM (like Claude 3.5 or GPT-4o) capable of executing strict Negative Constraints and complex human corrections.
