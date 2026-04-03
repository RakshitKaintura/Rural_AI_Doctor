from pydantic import BaseModel, Field
from typing import List, Optional


class RagUploadResponse(BaseModel):
    knowledge_base_id: str
    filename: str
    size_bytes: int
    chunks_indexed: int
    truncated: bool = False
    message: str


class RagQueryRequest(BaseModel):
    question: str = Field(..., min_length=3, description="Question about uploaded medical report content")
    top_k: int = Field(4, ge=1, le=10)


class RagCitation(BaseModel):
    id: int
    rank: int
    title: str
    source: Optional[str] = None
    excerpt: str


class RagQueryResponse(BaseModel):
    answer: str
    matched_chunks: int
    citations: List[RagCitation] = Field(default_factory=list)
