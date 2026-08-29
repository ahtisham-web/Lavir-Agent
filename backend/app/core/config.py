import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    APP_NAME: str = "Larvi Autonomous AI Agent"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Mode Settings
    DEFAULT_USE_MOCK: bool = os.getenv("USE_MOCK_DATA", "true").lower() == "true"
    
    # OAuth Credentials paths
    GOOGLE_CLIENT_SECRETS_FILE: str = os.getenv("GOOGLE_CLIENT_SECRETS_FILE", "credentials.json")
    GOOGLE_TOKEN_FILE: str = os.getenv("GOOGLE_TOKEN_FILE", "token.json")
    
    # Gemini / LLM Config
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # Security Safety Guard Thresholds
    REQUIRES_APPROVAL_FOR_SENDING_EMAIL: bool = True
    REQUIRES_APPROVAL_FOR_CANCELING_EVENT: bool = True
    REQUIRES_APPROVAL_FOR_CREATING_EVENT: bool = True

settings = Settings()
