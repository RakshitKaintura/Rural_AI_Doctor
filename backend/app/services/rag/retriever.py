from typing import List, Dict, Optional
from sqlalchemy import select, func
from sqlalchemy.orm import Session
# 2026 standard for pgvector integration
from pgvector.sqlalchemy import Vector
from app.db.models import MedicalDocument
from app.services.rag.embeddings import embedding_service
from app.core.config import settings

class VectorRetriever:
    def __init__(self, top_k: int = settings.TOP_K_RESULTS):
        self.top_k = top_k or settings.TOP_K_RESULTS
    
    def search(self, query: str, db: Session, top_k: Optional[int] = None) -> List[Dict]:
        """
        Vector similarity search using native SQLAlchemy pgvector operators.
        
        Args:
            query: Search query text
            db: Database session
            top_k: Number of results (overrides default)
            
        Returns:
            List of documents with similarity scores.
        """
        limit = top_k or self.top_k
        
        # 1. Generate query embedding (returns List[float])
        query_embedding = embedding_service.embed_query(query)
        
        # 2. Define the distance expression using the <=> operator
        # In 2026, .cosine_distance() is the native way to call this
        distance_expr = MedicalDocument.embedding.cosine_distance(query_embedding)
        
        # 3. Build the statement
        # We calculate similarity as (1 - distance)
        stmt = (
            select(
                MedicalDocument,
                (1 - distance_expr).label("similarity")
            )
            .where(MedicalDocument.embedding.is_not(None))
            .order_by(distance_expr)
            .limit(limit)
        )
        
        # 4. Execute and format
        results = db.execute(stmt).all()
        
        retrieved_docs = []
        for doc, similarity in results:
            retrieved_docs.append({
                "id": doc.id,
                "title": doc.title,
                "text": doc.content,
                "metadata": doc.metadata_json, # Using the renamed field from our model
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
        Vector search combined with metadata filtering using JSONB operators.
        
        Args:
            query: Search query
            db: Database session
            filters: e.g., {"source": "manual.pdf"}
            top_k: Number of results
        """
        limit = top_k or self.top_k
        query_embedding = embedding_service.embed_query(query)
        distance_expr = MedicalDocument.embedding.cosine_distance(query_embedding)
        
        # Build base statement
        stmt = select(
            MedicalDocument,
            (1 - distance_expr).label("similarity")
        ).where(MedicalDocument.embedding.is_not(None))
        
        # Add metadata filters dynamically
        if filters:
            for key, value in filters.items():
                # Uses the JSONB '->>' operator via SQLAlchemy
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

# Singleton instance
vector_retriever = VectorRetriever()