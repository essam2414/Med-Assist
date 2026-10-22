# Repository Guidelines

## Project Structure & Module Organization

- `med-assistant-web/backend/app/` contains the FastAPI application, split into `api/`, `models/`, `schemas/`, and `services/`. Backend utility scripts and sample data live under `backend/scripts/` and `backend/data/`.
- `med-assistant-web/frontend/src/` contains the React UI and styles; static files are in `frontend/public/` and `frontend/src/assets/`.
- `med-assistant-extension/` contains the Chrome extension pages, scripts, manifest, and icons.
- `vexa/` contains the meeting and transcription stack, Docker Compose configuration, libraries, and its own contributor documentation. `docs/` and the root Markdown files contain project and evaluation documentation.

## Build, Test, and Development Commands

Run app commands from the relevant directory:

- Backend: activate your virtual environment, install dependencies with `pip install -r requirements.txt`, then start the API using `uvicorn app.main:app --reload --port 8000`.
- Frontend: `npm install`, `npm run dev` for local development, `npm run build` to create a production build, and `npm run lint` to run ESLint.
- Vexa: from `vexa/`, start the local CPU stack with `docker compose -f docker-compose.yml -f docker-compose.local-db.yml --profile cpu up -d --force-recreate`.

## Coding Style & Naming Conventions

Follow nearby code style. Python modules and functions use `snake_case`; React components use `PascalCase` and JavaScript functions/variables use `camelCase`. Keep API routes, schemas, models, and service logic in their corresponding backend packages. Use the frontend ESLint rules (`npm run lint`) before submitting UI changes.

## Testing Guidelines

There is no single configured root test command. Backend files named `test_*.py` are primarily manual or service-dependent checks, and may require a running API, database, Ollama, or Vexa stack. Run only the checks relevant to your change and document any required services. For frontend changes, run `npm run lint` and `npm run build` from `med-assistant-web/frontend`.

## Commit & Pull Request Guidelines

Recent commits use short, imperative descriptions (for example, “Sanitize exposed keys and use env var for Vexa API token”). Keep commits focused and describe the change plainly. Pull requests should explain the user-visible or service-level impact, list validation performed, link related issues when applicable, and include screenshots for UI changes.

## Security & Configuration

Keep credentials and local configuration in ignored `.env` files; never commit tokens, API keys, or real patient data. Use the checked-in `env-example.*` files in `vexa/` as templates and configure local services as described in the root README.
