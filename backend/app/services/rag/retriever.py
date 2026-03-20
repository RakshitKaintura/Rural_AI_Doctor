from typing import List, Dict, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import MedicalDocument
from app.services.rag.embeddings import embedding_service
from app.core.config import settings

class VectorRetriever:
    """
    VectorRetriever handles semantic search and metadata filtering for medical documents.
    """
    
    def __init__(self, top_k: int = None):
        self.top_k = top_k or settings.TOP_K_RESULTS
    
    async def search(self, query: str, db: AsyncSession, top_k: Optional[int] = None) -> List[Dict]:
        
        limit = top_k or self.top_k
        query_embedding = embedding_service.embed_query(query)
        
        
        if not query_embedding or len(query_embedding) == 0:
            print(" Retriever: Embedding failed or returned empty. Skipping vector search.")
            return []
        
        
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

        try:
            result = await db.execute(stmt)
            results = result.all()
        except Exception as e:
            print(f" SQL Vector Search Error: {e}")
            return []
        
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

    async def search_with_filter(
        self,
        query: str,
        db: AsyncSession,
        filters: Optional[Dict] = None,
        top_k: Optional[int] = None
    ) -> List[Dict]:
        """
        Combined vector search and metadata filtering.
        """
        limit = top_k or self.top_k
        query_embedding = embedding_service.embed_query(query)
        
        # Safety Check
        if not query_embedding:
            return []
        
        distance_expr = MedicalDocument.embedding.cosine_distance(query_embedding)
        
        stmt = select(
            MedicalDocument,
            (1 - distance_expr).label("similarity")
        ).where(MedicalDocument.embedding.is_not(None))
        
        if filters:
            for key, value in filters.items():
            
                stmt = stmt.where(MedicalDocument.metadata_json[key].astext == str(value))
        
        stmt = stmt.order_by(distance_expr).limit(limit)
        
        try:
            result = await db.execute(stmt)
            results = result.all()
        except Exception:
            return []
        
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