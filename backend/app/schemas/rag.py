from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class DocumentUploadResponse(BaseModel):
    """Schema for document ingestion feedback."""
    message: str = Field(..., description="Success or error message")
    chunks_indexed: int = Field(..., description="Number of vector chunks created")
    document_id: Optional[int] = Field(None, description="Primary ID of the document in SQL")

class SearchRequest(BaseModel):
    """Schema for raw vector similarity searches."""
    query: str = Field(..., min_length=2, description="The search string or medical query")
    top_k: Optional[int] = Field(5, ge=1, le=20, description="Number of neighbors to return")
    filters: Optional[Dict] = Field(None, description="Metadata filters (e.g. {'source': 'manual.pdf'})")

class SearchResult(BaseModel):
    """Schema for an individual document chunk found in the vector DB."""
    id: int
    title: str
    text: str = Field(..., description="The actual text content of the chunk")
    similarity: float = Field(..., description="Cosine similarity score (0.0 to 1.0)")
    metadata: Dict = Field(..., description="Original file metadata and chunk indices")

class SearchResponse(BaseModel):
    """Schema for the full response of a vector search."""
    query: str
    results: List[SearchResult]
    total_results: int

from pydantic import BaseModel, Field
from typing import List, Optional

class RAGQueryRequest(BaseModel):
    """Schema for the incoming medical query."""
    question: str = Field(..., example="What is the treatment for acute asthma?")
    top_k: Optional[int] = Field(default=5, description="Number of document chunks to retrieve")
    include_sources: Optional[bool] = Field(default=True, description="Whether to return the source documents")

class RAGQueryResponse(BaseModel):
    """Schema for the final AI-generated medical answer."""
    question: str
    answer: str = Field(..., description="The AI's generated response based on retrieved data")
    sources: Optional[List[SearchResult]] = Field(None, description="List of documents used to ground the answer")