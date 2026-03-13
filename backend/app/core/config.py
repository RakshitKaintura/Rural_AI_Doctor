import os
import json
from typing import List, Union, Any
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Basic App Info ---
    ENVIRONMENT: str = "production"
    PROJECT_NAME: str = "Rural AI Doctor"
    VERSION: str = "1.1.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False  
    
    # --- Infrastructure ---

    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@127.0.0.1:5434/rural_ai_doctor"
    REDIS_URL: str = "memory://" 
    
    # --- Google AI & Vertex AI ---
    # Updated to the current production standard while keeping your location
    GOOGLE_API_KEY: str = ""
    GOOGLE_CLOUD_PROJECT: str = "" 
    VERTEX_AI_LOCATION: str = "us-central1"
    GOOGLE_APPLICATION_CREDENTIALS: str = ""
    GEMINI_MODEL: str = 'gemini-3.0-flash' # Standard 2026 stable release
    
    # --- RAG Settings ---
    EMBEDDING_MODEL: str = "models/text-multilingual-embedding-002"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    TOP_K_RESULTS: int = 3
    
    # --- Monitoring & Observability ---
    LANGCHAIN_TRACING_V2: bool = False # Default to False to save on API usage
    LANGCHAIN_API_KEY: str = "" 
    LANGCHAIN_PROJECT: str = "rural-ai-doctor"
    SENTRY_DSN: str = ""  

    # --- Security ---
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 # Increased for better UX
    
    # --- CORS Configuration ---
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> Union[List[str], str]:
        """Handles strings, comma-separated lists, and JSON arrays from ENV."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, str) and v.startswith("["):
            return json.loads(v)
        return v

    # --- Rate Limiting ---
    RATE_LIMIT_PER_MINUTE: int = 100

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()