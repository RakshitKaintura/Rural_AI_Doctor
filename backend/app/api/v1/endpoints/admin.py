"""
Admin endpoints for system-wide analytics and management.
"""

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models import User, Diagnosis, ChatHistory, VoiceInteraction, ImageAnalysis
from app.core.deps import get_current_admin_user

router = APIRouter(prefix="/admin", tags=["Admin Analytics"])

# Modern Dependency Aliases (2026 Best Practice)
DBDep = Annotated[AsyncSession, Depends(get_db)]
AdminDep = Annotated[User, Depends(get_current_admin_user)]

@router.get("/stats/overview")
async def get_admin_stats_overview(
    current_admin: AdminDep,
    db: DBDep
):
    """
    Retrieves global system metrics using optimized SQLAlchemy 2.0 scalar execution.
    """
    # Use timezone-aware UTC for 2026 standards
    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Global User Stats
    total_users = await db.scalar(select(func.count(User.id)))
    active_users = await db.scalar(
        select(func.count(User.id)).where(User.last_login >= thirty_days_ago)
    )

    # Diagnosis Analytics
    total_diagnoses = await db.scalar(select(func.count(Diagnosis.id)))
    diagnoses_today = await db.scalar(
        select(func.count(Diagnosis.id)).where(Diagnosis.created_at >= today_start)
    )

    # Feature Adoption Metrics
    total_chats = await db.scalar(
        select(func.count(func.distinct(ChatHistory.session_id)))
    )
    total_voice = await db.scalar(select(func.count(VoiceInteraction.id)))
    total_images = await db.scalar(select(func.count(ImageAnalysis.id)))

    return {
        "users": {
            "total": total_users or 0,
            "active_30_days": active_users or 0
        },
        "diagnoses": {
            "total": total_diagnoses or 0,
            "today": diagnoses_today or 0
        },
        "features": {
            "chat_sessions": total_chats or 0,
            "voice_interactions": total_voice or 0,
            "image_analyses": total_images or 0
        }
    }

@router.get("/stats/diagnoses-by-day")
async def get_diagnoses_by_day(
    db: DBDep,
    current_admin: AdminDep,
    days: int = 30
):
    """Retrieves time-series data for diagnosis trends."""
    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    query = (
        select(
            func.date(Diagnosis.created_at).label('date'),
            func.count(Diagnosis.id).label('count')
        )
        .where(Diagnosis.created_at >= start_date)
        .group_by(func.date(Diagnosis.created_at))
        .order_by(func.date(Diagnosis.created_at))
    )
    
    result = await db.execute(query)
    return [
        {"date": row.date.isoformat(), "count": row.count}
        for row in result.all()
    ]

@router.get("/stats/distribution")
async def get_global_distributions(current_admin: AdminDep, db: DBDep):
    """
    Aggregates global severity and urgency distributions.
    Demonstrates efficient grouping for data visualization.
    """
    # Severity Distribution
    sev_result = await db.execute(
        select(Diagnosis.severity, func.count(Diagnosis.id)).group_by(Diagnosis.severity)
    )
    
    # Urgency Distribution
    urg_result = await db.execute(
        select(Diagnosis.urgency_level, func.count(Diagnosis.id)).group_by(Diagnosis.urgency_level)
    )
    
    return {
        "severity": {sev: count for sev, count in sev_result.all()},
        "urgency": {urg: count for urg, count in urg_result.all()}
    }

@router.get("/users/recent")
async def get_recent_users(
    db: DBDep,
    current_admin: AdminDep,
    limit: int = 10
):
    """Retrieves the latest user registrations."""
    query = select(User).order_by(desc(User.created_at)).limit(limit)
    result = await db.execute(query)
    users = result.scalars().all()
    
    return [
        {
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role,
            "created_at": u.created_at,
            "last_login": u.last_login
        }
        for u in users
    ]

@router.get("/diagnoses/recent")
async def get_recent_diagnoses(
    db: DBDep,
    current_admin: AdminDep,
    limit: int = 10
):
    """Global feed of recent clinical activities."""
    query = select(Diagnosis).order_by(desc(Diagnosis.created_at)).limit(limit)
    result = await db.execute(query)
    diagnoses = result.scalars().all()
    
    return [
        {
            "id": d.id,
            "user_id": d.user_id,
            "diagnosis": d.diagnosis,
            "severity": d.severity,
            "urgency_level": d.urgency_level,
            "confidence": d.confidence,
            "created_at": d.created_at
        }
        for d in diagnoses
    ]