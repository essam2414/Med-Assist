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
from app.api.routes_chat import router as chat_router
from app.api.routes_recall import router as recall_router
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

from app.api.routes_recall import router as recall_router
from app.api.routes_ai_analytics import router as ai_analytics_router

app.include_router(root_router)
app.include_router(auth_router)
app.include_router(consultations_router)
app.include_router(transcripts_router)
app.include_router(insights_router)
app.include_router(patients_router)
app.include_router(chat_router)
app.include_router(recall_router)
app.include_router(ai_analytics_router)


@app.get("/health", tags=["health"])
async def health_check():
    import httpx
    from app.services.vexa_service import vexa_service
    
    gateway_status = "inactive"
    collector_status = "inactive"
    
    async with httpx.AsyncClient() as client:
        # Check Gateway
        try:
            await client.get(f"{vexa_service.gateway_base_url}/", timeout=1.0)
            gateway_status = "active"
        except Exception:
            gateway_status = "inactive"
            
        # Check Collector
        try:
            await client.get(f"{vexa_service.collector_base_url}/", timeout=1.0)
            collector_status = "active"
        except Exception:
            collector_status = "inactive"

    overall_status = "ok" if (gateway_status == "active" and collector_status == "active") else "error"
    
    return {
        "status": overall_status,
        "services": {
            "main_backend": "active",
            "vexa_gateway": gateway_status,
            "vexa_collector": collector_status
        }
    }

# DB session dependency you can use in routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()