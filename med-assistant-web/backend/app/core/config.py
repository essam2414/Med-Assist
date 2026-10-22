# backend/app/core/config.py
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    PROJECT_NAME: str = "Med Consult AI Backend"
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:5173", 
        "chrome-extension://*"
    ]
    SECRET_KEY: str = "change-this-in-prod"  # better: read from .env
    OPENAI_API_KEY: str  # will be loaded from .env
    ASSEMBLYAI_API_KEY: str
    RECALL_API_KEY: str
    RECALL_REGION: str = "us-east-1"
    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()