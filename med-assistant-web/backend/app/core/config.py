# backend/app/core/config.py
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    PROJECT_NAME: str = "Med Consult AI Backend"
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:5173"]
    SECRET_KEY: str = "change-this-in-prod"  # better: read from .env

    class Config:
        env_file = ".env"


settings = Settings()