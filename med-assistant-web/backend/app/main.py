# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.core.config import settings
from app.api.routes_root import router as root_router
from app.api.routes_consultations import router as consultations_router
from app.api.routes_transcripts import router as transcripts_router
from app.api.routes_insights import router as insights_router
from app.api.routes_auth import router as auth_router
from app.api.routes_patients import router as patients_router
from app.db import Base, engine, SessionLocal
import app.models  # noqa: F401  ensures models are imported so tables are known[web:178]

app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables (once, on startup)
Base.metadata.create_all(bind=engine)  # creates user, consultations, transcript_entries, ai_insights

app.include_router(root_router)
app.include_router(auth_router)
app.include_router(consultations_router)
app.include_router(transcripts_router)
app.include_router(insights_router)
app.include_router(patients_router)


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}

# DB session dependency you can use in routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()