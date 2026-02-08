from pydantic_settings import BaseSettings, SettingsConfigDict # Use SettingsConfigDict for v2
from typing import List

class Settings(BaseSettings):
    # App
    PROJECT_NAME: str = "Rural AI Doctor"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5434/rural_ai_doctor"
    
    # Google Cloud / Vertex AI
    # Pydantic will automatically look for GOOGLE_CLOUD_PROJECT in your .env
    GOOGLE_API_KEY: str = ""
    GOOGLE_CLOUD_PROJECT: str = "" 
    VERTEX_AI_LOCATION: str = "us-central1"
    GOOGLE_APPLICATION_CREDENTIALS: str = ""
    
    # LangSmith
    LANGCHAIN_TRACING_V2: bool = True
    LANGCHAIN_API_KEY: str = "" # No os.getenv needed here either
    LANGCHAIN_PROJECT: str = "rural-ai-doctor"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # Modern Pydantic v2 Configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()