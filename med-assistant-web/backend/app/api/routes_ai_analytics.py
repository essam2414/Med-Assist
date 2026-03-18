# backend/app/api/routes_ai_analytics.py
from datetime import date
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.ai_analytics import AIAnalyticsResponse
from app.services.ai_analytics_service import generate_weekly_analytics

router = APIRouter(
    prefix="/api/ai-analytics",
    tags=["ai-analytics"],
)

@router.get("/weekly", response_model=AIAnalyticsResponse)
async def get_weekly_analytics(
    target_date: date = Query(None, description="Date to determine the week. Defaults to today."),
    generate: bool = Query(False, description="Generate the AI summary"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if target_date is None:
        target_date = date.today()
        
    try:
        analytics = await generate_weekly_analytics(db, current_user.id, target_date, generate)
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
