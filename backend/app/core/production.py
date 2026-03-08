"""
Production-specific utilities for Rural AI Doctor.
Handles environment validation, directory provisioning, and connectivity health checks.
"""

import logging
import os
from pathlib import Path
from sqlalchemy import text
from app.db.session import engine, SessionLocal
from app.core.config import settings

logger = logging.getLogger(__name__)

def ensure_directories():
    """
    Provision necessary persistent storage directories.
    Ensures the application has write access to required paths.
    """
    # Base data directory is typically at the project root
    base_dir = Path(__file__).resolve().parent.parent.parent
    
    directories = [
        "logs",
        "data/raw/medical_pdfs",
        "data/uploads",
        "data/vector_store"
    ]
    
    for directory in directories:
        path = base_dir / directory
        try:
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Directory verified: {directory}")
        except Exception as e:
            logger.error(f"Failed to create directory {directory}: {e}")
            raise

def validate_environment():
    """
    Strict validation of critical environment variables.
    Fails fast if the application lacks credentials to operate.
    """
    required_vars = [
        "DATABASE_URL",
        "GOOGLE_API_KEY",
        "SECRET_KEY"
    ]
    
    missing_vars = [var for var in required_vars if not getattr(settings, var, None)]
    
    if missing_vars:
        error_msg = f"Missing critical environment variables: {', '.join(missing_vars)}"
        logger.error(f"❌ {error_msg}")
        raise ValueError(error_msg)
    
    logger.info("✅ Environment validation successful")

def check_database_connection():
    """
    Synchronous connectivity check for the database.
    Used during the bootstrapping process to ensure upstream readiness.
    """
    try:
        # Attempt a simple query to verify the connection pool is functional
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("✅ Database connectivity verified")
        return True
    except Exception as e:
        logger.error(f"❌ Database connectivity failed: {str(e)}")
        return False

def run_production_checks():
    """
    Master execution flow for production readiness.
    Called during the application lifespan startup.
    """
    logger.info("Initiating system readiness checks...")
    
    try:
        # 1. Provision storage
        ensure_directories()
        
        # 2. Validate secrets and config
        validate_environment()
        
        # 3. Verify downstream services
        if not check_database_connection():
            if settings.ENVIRONMENT == "production":
                raise ConnectionError("Database unreachable in production environment")
            logger.warning("Continuing startup despite database connection failure")
            
        logger.info("✅ System readiness checks complete")
        return True
    
    except Exception as e:
        logger.critical(f"Aborting startup due to failed readiness checks: {e}")
        raise