from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    # App Information
    PROJECT_NAME: str = "Rural AI Doctor"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True
    
    
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5434/rural_ai_doctor"
    
  
    GOOGLE_API_KEY: str = ""
    GOOGLE_CLOUD_PROJECT: str = "" 
    VERTEX_AI_LOCATION: str = "us-central1"
    GOOGLE_APPLICATION_CREDENTIALS: str = ""
    
   
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    TOP_K_RESULTS: int = 3
    
   
    LANGCHAIN_TRACING_V2: bool = True
    LANGCHAIN_API_KEY: str = "" 
    LANGCHAIN_PROJECT: str = "rural-ai-doctor"
    
  
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
 
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore" # This allows extra vars in .env without crashing, but won't add them to 'settings'
    )


settings = Settings()