
from typing import List, Dict, Optional
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from pgvector.sqlalchemy import Vector

from app.db.models import MedicalDocument
from app.services.rag.embeddings import embedding_service
from app.core.config import settings

class VectorRetriever:
    """
    VectorRetriever handles semantic search and metadata filtering for medical documents.
    Optimized for January 2026 standards using pgvector 0.3.6 and SQLAlchemy 2.0.46.
    """
    
    def __init__(self, top_k: int = settings.TOP_K_RESULTS):
        """
        Initialize the retriever with a default top_k value from configuration.
        """
        self.top_k = top_k or settings.TOP_K_RESULTS
    
    def search(self, query: str, db: Session, top_k: Optional[int] = None) -> List[Dict]:
        """
        Vector similarity search using native SQLAlchemy pgvector operators.
        Utilizes the text-embedding-004 model via the google-genai 1.1.0 client.
        
        Args:
            query: Search query text or symptoms string.
            db: Database session.
            top_k: Number of results to return (overrides default).
            
        Returns:
            List of documents with cosine similarity scores.
        """
        limit = top_k or self.top_k

        query_embedding = embedding_service.embed_query(query)
        
        distance_expr = MedicalDocument.embedding.cosine_distance(query_embedding)
        
        stmt = (
            select(
                MedicalDocument,
                (1 - distance_expr).label("similarity")
            )
            .where(MedicalDocument.embedding.is_not(None))
            .order_by(distance_expr)
            .limit(limit)
        )
 
        results = db.execute(stmt).all()
        
        retrieved_docs = []
        for doc, similarity in results:
            retrieved_docs.append({
                "id": doc.id,
                "title": doc.title,
                "text": doc.content,
                "metadata": doc.metadata_json,
                "similarity": float(similarity)
            })
        
        return retrieved_docs

    def search_with_filter(
        self,
        query: str,
        db: Session,
        filters: Optional[Dict] = None,
        top_k: Optional[int] = None
    ) -> List[Dict]:
        """
        Combined vector search and metadata filtering using native JSONB operators.
        Essential for filtering by specific medical manuals or indexed sessions.
        
        Args:
            query: Search query text.
            db: Database session.
            filters: Metadata filters, e.g., {"source": "pneumonia_guidelines.pdf"}.
            top_k: Number of results to return.
            
        Returns:
            Filtered list of documents with similarity scores.
        """
        limit = top_k or self.top_k
        
      
        query_embedding = embedding_service.embed_query(query)
        
        distance_expr = MedicalDocument.embedding.cosine_distance(query_embedding)
        
        stmt = select(
            MedicalDocument,
            (1 - distance_expr).label("similarity")
        ).where(MedicalDocument.embedding.is_not(None))
        
        if filters:
            for key, value in filters.items():

                stmt = stmt.where(MedicalDocument.metadata_json[key].astext == str(value))
        
        stmt = stmt.order_by(distance_expr).limit(limit)
        
        results = db.execute(stmt).all()
        
        return [
            {
                "id": doc.id,
                "title": doc.title,
                "text": doc.content,
                "metadata": doc.metadata_json,
                "similarity": float(similarity)
            }
            for doc, similarity in results
        ]

vector_retriever = VectorRetriever()