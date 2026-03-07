"""
Rural AI Doctor - FastAPI Main Application
Integrated with Structured Logging, Sentry, LangSmith, and Global Error Handling.
"""

import time
import logging
import uvicorn
import sentry_sdk
from prometheus_fastapi_instrumentator import Instrumentator
from sentry_sdk.integrations.fastapi import FastApiIntegration
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from slowapi.errors import RateLimitExceeded

# Core and Config
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.api.v1 import api_router

# Database Initialization
from app.db.base import Base 
from app.db.session import engine 
from app.db.models import ImageAnalysis 

# Middleware and Handlers
from app.middleware.error_handler import (
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)
from app.middleware.rate_limiter import limiter, rate_limit_exceeded_handler

#  Sentry Initialization 
if hasattr(settings, 'SENTRY_DSN') and settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment="development" if settings.DEBUG else "production",
        traces_sample_rate=1.0,
        integrations=[FastApiIntegration()],
        send_default_pii=False, 
        attach_stacktrace=True
    )

#  Setup Logging
log_level = "DEBUG" if settings.DEBUG else "INFO"
setup_logging(log_level)
logger = logging.getLogger(__name__)

if hasattr(settings, 'SENTRY_DSN') and settings.SENTRY_DSN:
    logger.info("Sentry error tracking enabled")

# Database Schema Sync
Base.metadata.create_all(bind=engine)

#  Create FastAPI instance
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs"
)
# Basic Health (You likely already have this)
@app.get("/health")
async def health():
    return {"status": "ok"}

#  Readiness Probe
@app.get("/ready")
async def ready():
    return {"status": "ready"}


@app.get("/live")
async def live():
    return {"status": "alive"}


@app.get("/health/detailed")
async def health_detailed():
    return {
        "status": "ok",
        "database": "connected",
        "vector_db": "ready",
        "version": "0.1.0"
    }


Instrumentator().instrument(app).expose(app)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

#  CORS Middleware
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
] + ([str(origin) for origin in settings.BACKEND_CORS_ORIGINS] if hasattr(settings, "BACKEND_CORS_ORIGINS") else [])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "X-Process-Time-MS"],
    max_age=600, 
)

#  Global Exception Handlers
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

#  Request Logging & Timing Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Logs every clinical API request and measures processing latency."""
    start_time = time.perf_counter()
    client_ip = request.client.host if request.client else "unknown"
    
    logger.info(
        f"Inbound Request: {request.method} {request.url.path}",
        extra={"ip": client_ip, "path": request.url.path}
    )
    
    response = await call_next(request)
    
    process_time = (time.perf_counter() - start_time) * 1000
    logger.info(
        f"Outbound Response: {response.status_code} | {process_time:.2f}ms",
        extra={
            "status_code": response.status_code,
            "duration_ms": round(process_time, 2),
            "path": request.url.path
        }
    )
    
    response.headers["X-Process-Time-MS"] = str(round(process_time, 2))
    return response

#  Route Registration
app.include_router(api_router, prefix=settings.API_V1_STR)

# Status, Health & Debug Endpoints
@app.get("/", tags=["Status"])
async def root():
    return {
        "message": "Rural AI Doctor API",
        "version": settings.VERSION,
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health", tags=["Status"])
async def health_check():
    return {"status": "healthy", "timestamp": time.time()}

@app.get("/sentry-debug", tags=["Debug"])
async def trigger_error():
    """Manual trigger to verify Sentry connection is working."""
    logger.warning("Sentry debug route triggered. Simulating a crash...")
    division_by_zero = 1 / 0
    return {"message": "This will not be reached"}

#  Lifecycle Events
@app.on_event("startup")
async def startup_event():
    logger.info(
        f"Bootstrapping {settings.PROJECT_NAME}",
        extra={
            "version": settings.VERSION,
            "db_engine": "PostgreSQL/pgvector",
            "embedding_model": "text-multilingual-embedding-002"
        }
    )

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)