import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "On-Call AI Incident Responder"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Validamos de forma temprana que la API key obligatoria esté configurada
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    if not GEMINI_API_KEY:
        raise ValueError("❌ CRÍTICO: La variable GEMINI_API_KEY no está configurada en el archivo .env")

settings = Settings()