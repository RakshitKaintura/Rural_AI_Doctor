"""
Rural AI Doctor - Unified Global Configuration
Merges existing Vertex AI settings with new Monitoring and Rate Limiting features.
"""

import os
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Basic App Info ---
    PROJECT_NAME: str = "Rural AI Doctor"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True
    
  
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@127.0.0.1:5434/rural_ai_doctor"
    REDIS_URL: str = "memory://"  # Required for RateLimiter (defaults to memory)
    
   
    GOOGLE_API_KEY: str = ""
    GOOGLE_CLOUD_PROJECT: str = "" 
    VERTEX_AI_LOCATION: str = "us-central1"
    GOOGLE_APPLICATION_CREDENTIALS: str = ""
    GEMINI_MODEL: str = 'gemini-2.5-flash' 
    
    
    EMBEDDING_MODEL: str = "models/text-multilingual-embedding-002"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    TOP_K_RESULTS: int = 3
    

    LANGCHAIN_TRACING_V2: bool = True
    LANGCHAIN_API_KEY: str = "" 
    LANGCHAIN_PROJECT: str = "rural-ai-doctor"
    SENTRY_DSN: str = ""  
    

    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
   
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        return v


    RATE_LIMIT_PER_MINUTE: int = 100

    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()