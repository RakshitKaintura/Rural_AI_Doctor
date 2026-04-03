import asyncio
import io
import re
import uuid
from typing import Any, List

import google.generativeai as genai
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pypdf import PdfReader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_active_user
from app.db.models import MedicalDocument, User
from app.db.session import get_db
from app.schemas.rag import RagCitation, RagQueryRequest, RagQueryResponse, RagUploadResponse
from app.services.llm.gemini_client import gemini_client


router = APIRouter()

MAX_PDF_UPLOAD_BYTES = 40 * 1024 * 1024
FALLBACK_EMBEDDING = [0.0] * 768


def _chunk_text(text: str, chunk_size: int = 2500, overlap: int = 250) -> List[str]:
    text = " ".join(text.split())
    if not text:
        return []

    chunks: List[str] = []
    start = 0
    text_len = len(text)
    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunks.append(text[start:end])
        if end >= text_len:
            break
        start = max(0, end - overlap)
    return chunks


def _extract_pdf_text(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    pages_text: List[str] = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        if page_text.strip():
            pages_text.append(page_text)
    return "\n\n".join(pages_text).strip()


def _tokenize(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) > 2}


def _score_chunk(question: str, content: str) -> float:
    q_terms = _tokenize(question)
    if not q_terms:
        return 0.0
    c_terms = _tokenize(content)
    overlap = len(q_terms & c_terms)
    phrase_bonus = 1.0 if question.lower() in content.lower() else 0.0
    return (overlap / len(q_terms)) + phrase_bonus


async def _embed_text(text: str) -> list[float]:
    if not settings.GOOGLE_API_KEY:
        return FALLBACK_EMBEDDING

    def _call_embed() -> list[float]:
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        result = genai.embed_content(
            model=settings.EMBEDDING_MODEL,
            content=text,
            task_type="retrieval_document",
        )
        embedding = result.get("embedding") if isinstance(result, dict) else None
        if isinstance(embedding, list) and len(embedding) == 768:
            return [float(v) for v in embedding]
        return FALLBACK_EMBEDDING

    try:
        return await asyncio.to_thread(_call_embed)
    except Exception:
        return FALLBACK_EMBEDDING


@router.post(
    "/upload-pdf",
    response_model=RagUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload PDF to personal RAG knowledge base",
)
async def upload_pdf_to_rag(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing file name")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    file_bytes = await file.read()
    size_bytes = len(file_bytes)
    if size_bytes > MAX_PDF_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="PDF exceeds 40MB size limit",
        )

    try:
        extracted_text = _extract_pdf_text(file_bytes)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to read PDF: {exc}") from exc

    if not extracted_text:
        raise HTTPException(status_code=400, detail="PDF contains no extractable text")

    chunks = _chunk_text(extracted_text)
    if not chunks:
        raise HTTPException(status_code=400, detail="No usable text chunks were produced")

    max_chunks = max(1, settings.RAG_MAX_CHUNKS_PER_DOC)
    truncated = len(chunks) > max_chunks
    if truncated:
        chunks = chunks[:max_chunks]

    kb_id = str(uuid.uuid4())
    created_rows: list[MedicalDocument] = []

    for idx, chunk in enumerate(chunks, start=1):
        embedding = await _embed_text(chunk)
        created_rows.append(
            MedicalDocument(
                title=f"{file.filename} (part {idx}/{len(chunks)})",
                content=chunk,
                embedding=embedding,
                metadata_json={
                    "source": file.filename,
                    "knowledge_base_id": kb_id,
                    "uploader_user_id": current_user.id,
                    "chunk_index": idx,
                    "chunk_total": len(chunks),
                },
            )
        )

    db.add_all(created_rows)
    await db.commit()

    return RagUploadResponse(
        knowledge_base_id=kb_id,
        filename=file.filename,
        size_bytes=size_bytes,
        chunks_indexed=len(chunks),
        truncated=truncated,
        message="PDF indexed successfully and ready for Q&A",
    )


@router.post(
    "/query",
    response_model=RagQueryResponse,
    summary="Ask questions over uploaded personal reports",
)
async def query_uploaded_reports(
    request: RagQueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    stmt = select(
        MedicalDocument.id,
        MedicalDocument.title,
        MedicalDocument.content,
        MedicalDocument.metadata_json,
    ).where(MedicalDocument.metadata_json["uploader_user_id"].astext == str(current_user.id))

    result = await db.execute(stmt)
    rows = list(result.all())

    if not rows:
        raise HTTPException(status_code=404, detail="No uploaded report data found. Upload a PDF first.")

    ranked = sorted(
        rows,
        key=lambda row: _score_chunk(request.question, row.content or ""),
        reverse=True,
    )

    top_rows = [row for row in ranked if _score_chunk(request.question, row.content or "") > 0][: request.top_k]
    if not top_rows:
        top_rows = ranked[: request.top_k]

    citations: list[RagCitation] = []
    context_blocks: list[str] = []
    for rank, row in enumerate(top_rows, start=1):
        metadata: Any = row.metadata_json if hasattr(row, "metadata_json") else {}
        source = ""
        if isinstance(metadata, dict):
            source = str(metadata.get("source") or "")

        excerpt = (row.content or "")[:700]
        citations.append(
            RagCitation(
                id=int(row.id),
                rank=rank,
                title=row.title or f"Chunk {rank}",
                source=source,
                excerpt=excerpt,
            )
        )
        context_blocks.append(f"[{rank}] {row.title}\n{row.content}")

    context_text = "\n\n".join(context_blocks)
    prompt = (
        "You are a medical report assistant. Answer ONLY from the provided context. "
        "If the context is insufficient, clearly say what is missing. "
        "Add citation markers like [1], [2] matching the context blocks.\n\n"
        f"Question:\n{request.question}\n\n"
        f"Context:\n{context_text}"
    )

    try:
        answer = await gemini_client.generate(prompt)
    except Exception:
        answer = (
            "I could not generate a model answer right now. "
            "Based on your uploaded report, please review the cited excerpts."
        )

    return RagQueryResponse(
        answer=str(answer),
        matched_chunks=len(citations),
        citations=citations,
    )
