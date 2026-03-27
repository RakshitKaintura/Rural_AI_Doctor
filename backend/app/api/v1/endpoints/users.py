"""
User management and dashboard analytics endpoints.
"""

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, desc, select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models import User, Diagnosis, ChatHistory, VoiceInteraction, ImageAnalysis
from app.core.deps import get_current_active_user
from app.schemas.user import UserDashboard, DiagnosisHistory, UserStats

router = APIRouter(prefix="/users", tags=["User Management"])

# Modern Dependency Aliases (2026 Best Practice)
DBDep = Annotated[AsyncSession, Depends(get_db)]
ActiveUser = Annotated[User, Depends(get_current_active_user)]


def _normalize_severity(value: str | None) -> str:
    """Normalize legacy severity labels to the API contract values."""
    mapping = {
        "low": "Low",
        "mild": "Low",
        "medium": "Medium",
        "moderate": "Medium",
        "high": "High",
        "severe": "High",
        "critical": "Critical",
    }
    normalized = mapping.get((value or "").strip().lower())
    return normalized or "Low"

@router.get("/dashboard", response_model=UserDashboard)
async def get_user_dashboard(current_user: ActiveUser, db: DBDep):
    """
    Retrieves aggregate statistics for the user dashboard using 
    optimized SQLAlchemy 2.0 scalar execution.
    """
    # Total counts using async execution
    total_diagnoses = await db.scalar(
        select(func.count(Diagnosis.id)).where(Diagnosis.user_id == current_user.id)
    )
    
    # Efficiently fetch top 5 recent records
    recent_query = (
        select(Diagnosis)
        .where(Diagnosis.user_id == current_user.id)
        .order_by(desc(Diagnosis.created_at))
        .limit(5)
    )
    recent_result = await db.execute(recent_query)
    recent_diagnoses = list(recent_result.scalars().all())
    for diagnosis in recent_diagnoses:
        diagnosis.severity = _normalize_severity(diagnosis.severity)
    
    # Interaction metrics
    total_chat_sessions = await db.scalar(
        select(func.count(func.distinct(ChatHistory.session_id)))
        .where(ChatHistory.user_id == current_user.id)
    )
    
    total_voice = await db.scalar(
        select(func.count(VoiceInteraction.id)).where(VoiceInteraction.user_id == current_user.id)
    )
    
    total_images = await db.scalar(
        select(func.count(ImageAnalysis.id)).where(ImageAnalysis.user_id == current_user.id)
    )
    
    # Get last activity timestamp
    last_act_query = (
        select(Diagnosis.created_at)
        .where(Diagnosis.user_id == current_user.id)
        .order_by(desc(Diagnosis.created_at))
    )
    last_activity = await db.scalar(last_act_query)
    
    return UserDashboard(
        total_diagnoses=total_diagnoses or 0,
        recent_diagnoses=list(recent_diagnoses),
        total_chat_sessions=total_chat_sessions or 0,
        total_voice_interactions=total_voice or 0,
        total_image_analyses=total_images or 0,
        last_activity=last_activity
    )

@router.get("/history/diagnoses", response_model=list[DiagnosisHistory])
async def get_diagnosis_history(
    db: DBDep,
    current_user: ActiveUser,
    skip: int = 0,
    limit: int = 10
):
    """Paginated retrieval of medical history."""
    query = (
        select(Diagnosis)
        .where(Diagnosis.user_id == current_user.id)
        .order_by(desc(Diagnosis.created_at))
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    diagnoses = list(result.scalars().all())
    for diagnosis in diagnoses:
        diagnosis.severity = _normalize_severity(diagnosis.severity)
    return diagnoses

@router.get("/stats", response_model=UserStats)
async def get_user_stats(current_user: ActiveUser, db: DBDep):
    """Calculates distribution analytics for medical insights."""
    
    # Severity breakdown
    sev_query = (
        select(Diagnosis.severity, func.count(Diagnosis.id))
        .where(Diagnosis.user_id == current_user.id)
        .group_by(Diagnosis.severity)
    )
    sev_result = await db.execute(sev_query)
    diagnoses_by_severity = {"Low": 0, "Medium": 0, "High": 0, "Critical": 0}
    for sev, count in sev_result.all():
        key = _normalize_severity(sev)
        diagnoses_by_severity[key] = diagnoses_by_severity.get(key, 0) + count
    
    # Time-series analysis (Last 6 Months)
    # Using timezone-aware UTC (2026 standard)
    six_months_ago = datetime.now(timezone.utc) - timedelta(days=180)
    
    monthly_query = (
        select(
            func.date_trunc('month', Diagnosis.created_at).label('month'),
            func.count(Diagnosis.id)
        )
        .where(Diagnosis.user_id == current_user.id, Diagnosis.created_at >= six_months_ago)
        .group_by('month')
    )
    monthly_result = await db.execute(monthly_query)
    diagnoses_by_month = {
        month.strftime('%Y-%m'): count for month, count in monthly_result.all()
    }
    
    # Mock data for demonstration - in production, this would use NLP symptom extraction
    most_common_symptoms = [
        {"symptom": "Fever", "count": 5},
        {"symptom": "Cough", "count": 3}
    ]
    
    return UserStats(
        diagnoses_by_severity=diagnoses_by_severity,
        diagnoses_by_month=diagnoses_by_month,
        most_common_symptoms=most_common_symptoms
    )

@router.delete("/history/diagnosis/{diagnosis_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_diagnosis(diagnosis_id: int, current_user: ActiveUser, db: DBDep):
    """Secure deletion of specific medical records."""
    # Atomic delete with ownership check
    stmt = (
        delete(Diagnosis)
        .where(Diagnosis.id == diagnosis_id, Diagnosis.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    await db.commit()
    
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Medical record not found or unauthorized"
        )
    
    return None