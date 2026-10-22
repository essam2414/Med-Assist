# backend/app/core/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Med Consult AI Backend"
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:5173", 
        "chrome-extension://*"
    ]
    SECRET_KEY: str = "change-this-in-prod"  # better: read from .env
    # The application uses local Ollama and the self-hosted Vexa stack.
    # These settings are optional so the backend can start without legacy vendor keys.
    VEXA_API_KEY: str = ""
    VEXA_GATEWAY_URL: str = "http://localhost:8056"
    VEXA_COLLECTOR_URL: str = "http://localhost:8123"
    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
