"""
Admin endpoints for system-wide analytics and management.
"""

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import case, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models import (
    AIDecisionAudit,
    ChatHistory,
    Diagnosis,
    ImageAnalysis,
    Patient,
    User,
    VoiceInteraction,
)
from app.core.deps import get_current_admin_user
from app.schemas.admin import (
    AdminAuditFeedbackResponse,
    AdminAuditFeedbackUpdateRequest,
    AdminAuditLogsResponse,
    AdminAuditSessionResponse,
    AdminBiasCheckResponse,
)

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


@router.get("/audit/logs", response_model=AdminAuditLogsResponse)
async def get_audit_logs(
    current_admin: AdminDep,
    db: DBDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    q: str | None = Query(default=None, description="Search query over input/output/model/session"),
):
    """Paginated deep-dive list of AI decision audits."""
    base_query = select(AIDecisionAudit)

    if q:
        search = f"%{q.strip()}%"
        base_query = base_query.where(
            or_(
                AIDecisionAudit.input_summary.ilike(search),
                AIDecisionAudit.output_summary.ilike(search),
                AIDecisionAudit.model_name.ilike(search),
                AIDecisionAudit.decision_type.ilike(search),
                AIDecisionAudit.session_id.ilike(search),
            )
        )

    count_query = select(func.count()).select_from(base_query.subquery())
    total = int((await db.scalar(count_query)) or 0)

    offset = (page - 1) * page_size
    result = await db.execute(
        base_query.order_by(desc(AIDecisionAudit.created_at)).offset(offset).limit(page_size)
    )
    rows = result.scalars().all()

    return {
        "items": [
            {
                "id": row.id,
                "session_id": row.session_id,
                "source_endpoint": row.source_endpoint,
                "decision_type": row.decision_type,
                "input_summary": row.input_summary,
                "output_summary": row.output_summary,
                "confidence_band": row.confidence_band,
                "urgency_level": row.urgency_level,
                "model_name": row.model_name,
                "model_version": row.model_version,
                "prompt_version": row.prompt_version,
                "override_applied": row.override_applied,
                "clinician_feedback": row.clinician_feedback,
                "created_at": row.created_at,
            }
            for row in rows
        ],
        "page": page,
        "page_size": page_size,
        "total": total,
    }


@router.get("/audit/sessions/{session_id}", response_model=AdminAuditSessionResponse)
async def get_audit_session_history(
    session_id: str,
    current_admin: AdminDep,
    db: DBDep,
):
    """Fetch full chat transcript for an audited session."""
    audit_exists = await db.scalar(
        select(func.count(AIDecisionAudit.id)).where(AIDecisionAudit.session_id == session_id)
    )
    if not audit_exists:
        raise HTTPException(status_code=404, detail="No audit log found for this session")

    result = await db.execute(
        select(ChatHistory)
        .where(ChatHistory.session_id == session_id)
        .order_by(ChatHistory.created_at.asc())
    )
    messages = result.scalars().all()

    return {
        "session_id": session_id,
        "messages": [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at,
            }
            for msg in messages
        ],
    }


@router.patch("/audit/{audit_id}/feedback", response_model=AdminAuditFeedbackResponse)
async def update_audit_feedback(
    audit_id: int,
    payload: AdminAuditFeedbackUpdateRequest,
    current_admin: AdminDep,
    db: DBDep,
):
    """Save clinician feedback and override toggle for an AI decision record."""
    result = await db.execute(select(AIDecisionAudit).where(AIDecisionAudit.id == audit_id))
    audit_row = result.scalar_one_or_none()
    if audit_row is None:
        raise HTTPException(status_code=404, detail="Audit log not found")

    audit_row.clinician_feedback = payload.clinician_feedback
    audit_row.override_applied = payload.override_applied
    await db.commit()
    await db.refresh(audit_row)

    return {
        "id": audit_row.id,
        "override_applied": audit_row.override_applied,
        "clinician_feedback": audit_row.clinician_feedback,
        "updated": True,
    }


@router.get("/analytics/bias-check", response_model=AdminBiasCheckResponse)
async def get_bias_check_analytics(
    current_admin: AdminDep,
    db: DBDep,
):
    """Demographic distributions for urgency and confidence (gender/age groups)."""
    age_group = case(
        (Patient.age.is_(None), "Unknown"),
        (Patient.age < 18, "0-17"),
        (Patient.age < 36, "18-35"),
        (Patient.age < 61, "36-60"),
        else_="60+",
    ).label("age_group")

    confidence_band = case(
        (Diagnosis.confidence.is_(None), "Unknown"),
        (Diagnosis.confidence < 0.40, "Low"),
        (Diagnosis.confidence < 0.75, "Medium"),
        else_="High",
    ).label("confidence_band")

    gender_urgency_rows = (
        await db.execute(
            select(
                func.coalesce(Patient.gender, "Unknown").label("demographic"),
                Diagnosis.urgency_level.label("urgency_level"),
                func.count(Diagnosis.id).label("count"),
            )
            .outerjoin(Patient, Diagnosis.patient_id == Patient.id)
            .group_by(func.coalesce(Patient.gender, "Unknown"), Diagnosis.urgency_level)
            .order_by(func.coalesce(Patient.gender, "Unknown"), Diagnosis.urgency_level)
        )
    ).all()

    gender_confidence_rows = (
        await db.execute(
            select(
                func.coalesce(Patient.gender, "Unknown").label("demographic"),
                confidence_band,
                func.count(Diagnosis.id).label("count"),
            )
            .outerjoin(Patient, Diagnosis.patient_id == Patient.id)
            .group_by(func.coalesce(Patient.gender, "Unknown"), confidence_band)
            .order_by(func.coalesce(Patient.gender, "Unknown"), confidence_band)
        )
    ).all()

    age_urgency_rows = (
        await db.execute(
            select(
                age_group,
                Diagnosis.urgency_level.label("urgency_level"),
                func.count(Diagnosis.id).label("count"),
            )
            .outerjoin(Patient, Diagnosis.patient_id == Patient.id)
            .group_by(age_group, Diagnosis.urgency_level)
            .order_by(age_group, Diagnosis.urgency_level)
        )
    ).all()

    age_confidence_rows = (
        await db.execute(
            select(
                age_group,
                confidence_band,
                func.count(Diagnosis.id).label("count"),
            )
            .outerjoin(Patient, Diagnosis.patient_id == Patient.id)
            .group_by(age_group, confidence_band)
            .order_by(age_group, confidence_band)
        )
    ).all()

    return {
        "gender_urgency": [
            {
                "demographic": row.demographic or "Unknown",
                "urgency_level": row.urgency_level or "UNKNOWN",
                "count": int(row.count or 0),
            }
            for row in gender_urgency_rows
        ],
        "gender_confidence": [
            {
                "demographic": row.demographic or "Unknown",
                "confidence_band": row.confidence_band or "Unknown",
                "count": int(row.count or 0),
            }
            for row in gender_confidence_rows
        ],
        "age_urgency": [
            {
                "demographic": row.age_group or "Unknown",
                "urgency_level": row.urgency_level or "UNKNOWN",
                "count": int(row.count or 0),
            }
            for row in age_urgency_rows
        ],
        "age_confidence": [
            {
                "demographic": row.age_group or "Unknown",
                "confidence_band": row.confidence_band or "Unknown",
                "count": int(row.count or 0),
            }
            for row in age_confidence_rows
        ],
    }
