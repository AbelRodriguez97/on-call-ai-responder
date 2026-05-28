import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "On-Call AI Incident Responder"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # Optional — if not set, Slack notifications are silently skipped
    SLACK_WEBHOOK_URL: str = os.getenv("SLACK_WEBHOOK_URL", "")

    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY no está configurada en el archivo .env")

settings = Settings()