# backend/app/models/__init__.py
from app.db import Base  # noqa
from app.models.user import User  # noqa
from app.models.consultation import Consultation  # noqa
from app.models.transcript import TranscriptEntry  # noqa
from app.models.insight import AIInsight  # noqa
from app.models.patient import Patient  # noqa
from app.models.chat import ChatSession, ChatMessage  # noqa
from app.models.live_insight import LiveInsight  # noqa
from app.models.ai_analytics import AIAnalytics  # noqa
