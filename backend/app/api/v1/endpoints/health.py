"""
Optimized Health Check and System Monitoring for Rural AI Doctor.
Ensures high availability through dependency validation and resource tracking.
"""
from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.ext.asyncio import AsyncSession # Updated for Async compatibility
from sqlalchemy import text
import psutil
import time
from datetime import datetime, timezone
from app.db.session import get_db
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/health", status_code=status.HTTP_200_OK, tags=["Monitoring"])
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "Rural AI Doctor API",
        "version": getattr(settings, "VERSION", "0.1.0")
    }

@router.get("/health/detailed", tags=["Monitoring"])
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    """Comprehensive vitals: Checks Database, AI SDK, and Cache state."""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": {}
    }
    
    try:
        await db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = {"status": "up", "type": "PostgreSQL/pgvector"}
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = {"status": "down", "error": str(e)}

    #  Redis/Cache Configuration Check
    health_status["checks"]["cache"] = {
        "status": "configured" if getattr(settings, "REDIS_URL", None) else "local_memory",
    }

    #  Clinical AI Engine Check
    health_status["checks"]["gemini_api"] = {
        "status": "ready" if settings.GOOGLE_API_KEY else "missing_key",
        "chat_model": settings.GEMINI_MODEL,
        "embedding_supported": True
    }
    
    if health_status["status"] == "unhealthy":
        logger.critical(f"HEALTH FAILURE: {health_status['checks']}")
        
    return health_status

@router.get("/metrics", tags=["Monitoring"])
async def get_metrics():
    """Real-time system telemetry for Prometheus/Grafana style tracking."""
    cpu_percent = psutil.cpu_percent(interval=None) # Non-blocking call
    memory = psutil.virtual_memory()
    process = psutil.Process()
    
    return {
        "system": {
            "cpu_utilization": f"{cpu_percent}%",
            "memory_usage": f"{memory.percent}%",
            "disk_utilization": f"{psutil.disk_usage('/').percent}%"
        },
        "process": {
            "memory_mb": round(process.memory_info().rss / (1024 * 1024), 2),
            "uptime_sec": round(time.time() - process.create_time(), 2),
            "thread_count": process.num_threads()
        }
    }

@router.get("/ready", tags=["Monitoring"])
async def readiness_check(response: Response, db: AsyncSession = Depends(get_db)):
    
    try:
        await db.execute(text("SELECT 1"))
        if not settings.GOOGLE_API_KEY:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            return {"status": "not_ready", "reason": "AI engine offline"}
        return {"status": "ready"}
    except Exception:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "not_ready", "reason": "Database unavailable"}

@router.get("/live", tags=["Monitoring"])
async def liveness_check():

    return {"status": "alive"}