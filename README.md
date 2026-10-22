# Med-Assist (EUS328 Final Year Project)

Med-Assist is a clinician-focused platform that supports online consultations with AI-assisted documentation, recall, and review.

It is built to help doctors:
- capture and structure consultation conversations
- generate live and post-consultation insights
- query patient history with natural-language questions
- summarize weekly consultation activity for faster follow-up

This repository includes the complete stack used in the project, including the Med-Assist web app, browser extension, and integrated Vexa meeting intelligence services.

## Tech Stack

- **Frontend:** React 19, Vite, JavaScript, CSS
- **Backend API:** FastAPI, Uvicorn, Pydantic
- **Database:** SQLite with SQLAlchemy ORM
- **Authentication:** JWT + HTTP-only cookies (`python-jose`, `passlib`)
- **AI Layer:** Ollama-hosted LLMs (`llama3.1`, `llama3.2`) via LangChain/LangGraph
- **Retrieval:** FAISS + HuggingFace embeddings for transcript-backed patient querying
- **Meeting/Transcription Integration:** Vexa services (bot orchestration + transcript collection)
- **Runtime/Infra:** Docker Compose (Vexa), local Python and Node.js app runtime

## Architecture Overview

The system is organized into four main parts:

1. **`med-assistant-web/frontend`**  
   Doctor-facing dashboard for consultations, patient management, Ask AI chat, live insights, and weekly analytics.

2. **`med-assistant-web/backend`**  
   FastAPI service that handles auth, patients, consultations, transcripts, AI insight generation, weekly analytics, and RAG-powered chat over patient records.

3. **`med-assistant-extension`**  
   Chrome side-panel companion that monitors active consultations and displays live AI insight updates in real time.

4. **`vexa`**  
   Self-hosted meeting intelligence stack used to join calls and stream transcript segments back to Med-Assist.

### High-Level Data Flow

1. Doctor creates or opens a consultation in the web app.
2. Backend can connect a Vexa bot to a meeting URL for live sessions.
3. Transcript segments are synced into Med-Assist and stored in SQLite.
4. Live insight workers generate incremental AI updates while the consultation is active.
5. After/during the session, clinicians can generate structured insights, query patient history with Ask AI, and review weekly summaries.
6. The browser extension polls authenticated backend endpoints to show current consultation status and live insight cards.

---

## 🚀 Quick Start Guide

### 1. Vexa (Meeting Intelligence)
Vexa handles bot joining, recording, and real-time transcription. Start it from the `vexa` directory.

```powershell
cd vexa
docker compose -f docker-compose.yml -f docker-compose.local-db.yml --profile cpu up -d --force-recreate
```

### 2. Backend & AI Setup (FastAPI + Ollama)
The backend manages Med-Assist logic and uses local LLM inference via Ollama.

#### A. Install Python Dependencies
```powershell
cd med-assistant-web/backend
.\.venv\Scripts\Activate
pip install -r requirements.txt
```

#### B. Download Ollama Models
```powershell
ollama pull llama3.1
ollama pull llama3.2
```

#### C. Start Backend
```powershell
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend (React + Vite)
```powershell
cd med-assistant-web/frontend
npm install
npm run dev
```

---

## 🛠️ Maintenance & Monitoring

- **Vexa logs:** `docker compose logs -f whisperlive-cpu`
- **Stop Vexa:** `docker compose down`
- **Backend/frontend stop:** `Ctrl + C` in their terminals
