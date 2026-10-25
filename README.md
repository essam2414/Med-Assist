# Med-Assist (EUS328 Final Year Project) Achieved 82% grade.

Med-Assist is a clinician-focused consultation app with AI-assisted documentation, patient history chat, live insights, and weekly summaries. It's main feature is a locally hosted meeting bot joining an online meeting during a consultation and transcribing the audio and feeding it into a local AI system for live insights. The project does not use any third party infrastructure adhering to NHS guidelines. This repository contains the React web app, FastAPI backend, Chrome extension, and a local Vexa meeting-bot/transcription stack.

## Requirements

For the full local setup, install [Docker Desktop](https://docs.docker.com/desktop/setup/install/windows-install/) with its Linux container/WSL 2 backend, [Git](https://git-scm.com/downloads), [Python 3.11](https://www.python.org/downloads/), [Node.js LTS](https://nodejs.org/en/download), and [Ollama](https://ollama.com/download). Python 3.11 is recommended for the backend's ML dependencies. The Vexa CPU profile downloads Whisper models and can take several minutes and several GB of disk space on first build/run. A Google Meet account and an active meeting are needed to verify bot joining. No OpenAI, Recall.ai, or AssemblyAI account is needed for the normal app path.

## First-Time Setup

If you have not downloaded the repository yet, clone it and enter the project folder:

```powershell
git clone https://github.com/essam2414/Med-Assist.git
cd Med-Assist
```

Then use PowerShell from the repository root. Keep Docker Desktop running throughout the Vexa steps.

### 1. Start local Vexa services

```powershell
cd vexa
Copy-Item env-example.cpu .env
```

For a private local development setup, change `ADMIN_API_TOKEN` in `vexa/.env` from its example value to a unique secret. `env-example.cpu` also contains a sample remote-transcriber key, but the CPU profile below does not use it. Then build and start the CPU transcription stack (first run may take a while):

```powershell
docker compose -f docker-compose.yml -f docker-compose.local-db.yml --profile cpu up -d --build
```

Check that containers are up with `docker compose -f docker-compose.yml -f docker-compose.local-db.yml --profile cpu ps`. Open `http://localhost:8056/docs` to check the Vexa API. The Compose stack uses its bundled local PostgreSQL database and the self-hosted CPU WhisperLive transcriber; it does not require a remote transcription API key.

Create the application user and a Vexa client token after the stack is running:

```powershell
python create_key.py
```

Copy the printed `VEXA_TOKEN` value for the backend configuration. The script reads the admin token from `vexa/.env` and creates a client token in Vexa's database. Keep both tokens private.

### 2. Configure and start the backend

```powershell
cd ..\med-assistant-web\backend
notepad .env
```

This opens Notepad in the backend folder. If Windows asks whether to create the file, choose **Yes**. Paste the following lines, replace the two example values, then save the file as `.env` (make sure Notepad does not add a `.txt` extension):

```dotenv
SECRET_KEY=replace-with-a-long-random-secret
VEXA_API_KEY=paste-the-VEXA_TOKEN-here
VEXA_GATEWAY_URL=http://localhost:8056
VEXA_COLLECTOR_URL=http://localhost:8123
```

Ollama's Windows installer runs a local service. Download the app's models before using the AI features:

```powershell
ollama pull llama3.1
ollama pull llama3.2
```

Then install and start the API:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The app uses SQLite at `backend/med_assistant.db`; it creates its tables when the API starts. On first backend startup, the `all-MiniLM-L6-v2` sentence embedding model may download from Hugging Face. Keep Ollama running while using AI features. The backend starts without the Vexa token, but joining a meeting requires a valid `VEXA_API_KEY` generated in step 1.

When Uvicorn reports that it is running, check `http://localhost:8000/health`; its Vexa service statuses should both be `active` when the Vexa stack is up.

### 3. Start the frontend

In another PowerShell window:

```powershell
cd med-assistant-web\frontend
npm install
npm run dev
```

Open the local URL printed by Vite (normally `http://localhost:5173`), create an account, and sign in.

### 4. Install the Chrome extension (optional)

Open `chrome://extensions`, enable **Developer mode**, choose **Load unpacked**, and select this repository's `med-assistant-extension` folder. Open the extension's **Options** page and set the backend URL to `http://localhost:8000` and dashboard URL to `http://localhost:5173`. The extension requires the backend to be running.

## Joining a Meeting and Getting Transcripts

Create or open a consultation in the web app, enter a Google Meet URL, and use the app's connect action. The Vexa bot joins as a participant; admit it from the Meet waiting room if required. Once admitted and the meeting has active speech, Vexa's local Whisper service sends transcript segments to the collector and the backend syncs them to the consultation. Use the app's disconnect action to stop the bot and sync final segments. The bot only supports Google Meet in this integration. Tell participants that transcription is active and obtain any required consent before capturing clinical information.

If connection fails, check the backend terminal and Vexa logs:

```powershell
cd vexa
docker compose -f docker-compose.yml -f docker-compose.local-db.yml --profile cpu logs -f
```

Verify `VEXA_API_KEY` matches the generated client token, Vexa containers are healthy, ports 8056 and 8123 are available, and the Meet bot has been admitted. Stop Vexa with the same Compose files and `down`.

## Development and Validation

From `med-assistant-web/frontend`, use `npm run lint` and `npm run build`. From `med-assistant-web/backend`, activate `.venv` and run `uvicorn app.main:app --reload --port 8000`. Backend `test_*.py` files are mostly manual or evaluation scripts and can require running services; inspect a script before running it. Vexa has its own setup and contributor notes in `vexa/README.md` and `vexa/CONTRIBUTING.md`.

## Configuration and Architecture

The frontend is in `med-assistant-web/frontend/src`. The API routes, SQLAlchemy models, Pydantic schemas, and service logic are under `med-assistant-web/backend/app/{api,models,schemas,services}`. The Chrome extension is in `med-assistant-extension`; Vexa services, compose files, and CPU transcription code are under `vexa/`.

The normal runtime uses local Ollama for language models and local Vexa for meeting transcription. `RECALL_API_KEY` and `ASSEMBLYAI_API_KEY` are not needed by the main app flow; the latter appears in a standalone AssemblyAI check script. `OPENAI_API_KEY` is optional for the legacy uploaded-audio transcription endpoint (`/transcripts/upload`), which uses OpenAI Whisper; live Meet transcription goes through Vexa instead. Never commit `.env` files, generated Vexa tokens, real patient information, or secrets. `LANGCHAIN_API_KEY` is optional and only needed for LangSmith tracing.
