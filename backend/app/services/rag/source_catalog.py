from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import or_, select

from app.core.config import settings
from app.db.models import MedicalEvidenceSource
from app.db.session import AsyncSessionLocal


def _trim_excerpt(text: str, max_len: int = 420) -> str:
    normalized = " ".join((text or "").split())
    if len(normalized) <= max_len:
        return normalized
    return normalized[:max_len].rstrip() + "..."


def _provider_weight(provider: str) -> float:
    weights = {
        "WHO": 1.0,
        "CDC": 0.98,
        "NICE": 0.97,
        "PubMed": 0.95,
        "OpenFDA": 0.92,
        "MedlinePlus": 0.9,
        "ClinicalTrials": 0.86,
        "LocalRAG": 0.84,
    }
    return weights.get(provider, 0.8)


def _evidence_level_weight(level: str | None) -> float:
    weights = {
        "guideline": 1.0,
        "systematic_review": 0.98,
        "rct": 0.95,
        "meta_analysis": 0.95,
        "observational": 0.85,
        "expert_consensus": 0.8,
        "reference": 0.75,
    }
    if not level:
        return 0.75
    return weights.get(level.strip().lower(), 0.75)


async def embed_text(text: str, task_type: str = "retrieval_document") -> list[float] | None:
    if not settings.GOOGLE_API_KEY:
        return None

    def _call_embed() -> list[float] | None:
        try:
            import google.generativeai as genai
        except Exception:
            return None
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        result = genai.embed_content(
            model=settings.EMBEDDING_MODEL,
            content=text,
            task_type=task_type,
        )
        embedding = result.get("embedding") if isinstance(result, dict) else None
        return embedding if isinstance(embedding, list) else None

    try:
        return await asyncio.to_thread(_call_embed)
    except Exception:
        return None


async def retrieve_catalog_citations(query: str, top_k: int = 4) -> list[dict[str, Any]]:
    """Retrieve references from curated, database-backed medical evidence sources."""
    citations: list[dict[str, Any]] = []
    query_embedding = await embed_text(query, task_type="retrieval_query")

    async with AsyncSessionLocal() as db:
        rows = []
        if query_embedding:
            try:
                vector_stmt = (
                    select(
                        MedicalEvidenceSource,
                        (1 - MedicalEvidenceSource.embedding.cosine_distance(query_embedding)).label("similarity"),
                    )
                    .where(
                        MedicalEvidenceSource.is_active.is_(True),
                        MedicalEvidenceSource.embedding.is_not(None),
                    )
                    .order_by(MedicalEvidenceSource.embedding.cosine_distance(query_embedding))
                    .limit(top_k)
                )
                vector_result = await db.execute(vector_stmt)
                rows = list(vector_result.all())
            except Exception:
                rows = []

        if not rows:
            lexical_stmt = (
                select(MedicalEvidenceSource)
                .where(
                    MedicalEvidenceSource.is_active.is_(True),
                    or_(
                        MedicalEvidenceSource.title.ilike(f"%{query}%"),
                        MedicalEvidenceSource.excerpt.ilike(f"%{query}%"),
                    ),
                )
                .limit(top_k)
            )
            lexical_result = await db.execute(lexical_stmt)
            rows = [(item, 0.0) for item in lexical_result.scalars().all()]

        for rank, (source, similarity) in enumerate(rows, start=1):
            provider = str(source.provider or "Catalog")
            weighted_similarity = float(similarity or 0.0) * _provider_weight(provider) * _evidence_level_weight(source.evidence_level)
            citations.append(
                {
                    "id": int(source.id),
                    "rank": rank,
                    "provider": provider,
                    "title": source.title,
                    "source": source.url,
                    "excerpt": _trim_excerpt(source.excerpt),
                    "similarity": weighted_similarity,
                    "evidence_level": source.evidence_level,
                    "published_at": source.published_at.isoformat() if source.published_at else None,
                    "last_verified_at": source.last_verified_at.isoformat() if source.last_verified_at else None,
                }
            )

    citations.sort(key=lambda c: float(c.get("similarity", 0.0)), reverse=True)
    for idx, citation in enumerate(citations, start=1):
        citation["rank"] = idx
    return citations[: max(1, top_k)]


def default_trusted_sources() -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc)
    return [
        {
            "provider": "WHO",
            "title": "Integrated Management of Childhood Illness (IMCI) - Chart Booklet",
            "url": "https://www.who.int/publications/i/item/9789241506823",
            "excerpt": "Evidence-based triage and referral guidance for low-resource care settings, including danger signs and urgent referral criteria.",
            "condition_tags": ["pediatrics", "triage", "rural-care"],
            "evidence_level": "guideline",
            "published_at": now,
            "last_verified_at": now,
        },
        {
            "provider": "CDC",
            "title": "Antibiotic Prescribing and Use in Doctor's Offices",
            "url": "https://www.cdc.gov/antibiotic-use/index.html",
            "excerpt": "Guidance for safe antibiotic stewardship and indication-based prescribing to reduce unnecessary antimicrobial exposure.",
            "condition_tags": ["antibiotics", "respiratory", "stewardship"],
            "evidence_level": "guideline",
            "published_at": now,
            "last_verified_at": now,
        },
        {
            "provider": "NICE",
            "title": "Fever in under 5s: assessment and initial management",
            "url": "https://www.nice.org.uk/guidance/ng143",
            "excerpt": "Risk stratification and first-pass management recommendations for pediatric fever, including red-flag pathways.",
            "condition_tags": ["fever", "pediatrics", "triage"],
            "evidence_level": "guideline",
            "published_at": now,
            "last_verified_at": now,
        },
    ]
