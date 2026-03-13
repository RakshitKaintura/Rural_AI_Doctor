import logging
import numpy as np
from typing import List
from google import genai
from google.genai import types
from app.core.config import settings

# Initialize logging for production monitoring
logger = logging.getLogger(__name__)

# Initialize the Gemini Client using the centralized configuration
client = genai.Client(
    api_key=settings.GOOGLE_API_KEY
)

class EmbeddingService:
    """
    Service for generating vector embeddings via Gemini API.
    Optimized for RAG (Retrieval-Augmented Generation) in medical contexts.
    """
    def __init__(self):
        # text-multilingual-embedding-002 is highly effective for rural contexts
        # where medical symptoms might be described in regional dialects or mixed languages.
        self.model_name = "models/text-multilingual-embedding-002" 
        self.dimensions = 768 

    def _get_embedding(self, text: str, task_type: str) -> List[float]:
        """
        Internal method to fetch embeddings with specific task types.
        """
        try:
            clean_text = text.strip()
            if not clean_text:
                logger.warning("Attempted to embed an empty string.")
                return []

            # Call the Gemini Embedding API
            # Task types (RETRIEVAL_DOCUMENT vs RETRIEVAL_QUERY) optimize the 
            # vector space for better matching.
            response = client.models.embed_content(
                model=self.model_name,
                contents=clean_text,
                config=types.EmbedContentConfig(
                    task_type=task_type,
                    output_dimensionality=self.dimensions
                )
            )
            
            if response and response.embeddings:
                # Return the values for the first content item
                return response.embeddings[0].values
            
            logger.warning(f"Empty embedding returned for model {self.model_name}")
            return []
            
        except Exception as e:
            logger.error(f"Embedding failed for {self.model_name}: {str(e)}")
            return []

    def embed_text(self, text: str) -> List[float]:
        """
        Convert medical document chunks into vectors for indexing.
        Uses RETRIEVAL_DOCUMENT task type for static content.
        """
        return self._get_embedding(text, "RETRIEVAL_DOCUMENT")

    def embed_query(self, query: str) -> List[float]:
        """
        Convert user symptom descriptions into vectors for search.
        Uses RETRIEVAL_QUERY task type to optimize against indexed documents.
        """
        return self._get_embedding(query, "RETRIEVAL_QUERY")
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Batch process for bulk indexing medical documents.
        Significantly reduces API latency and prevents rate-limit hits.
        """
        try:
            # Filter empty strings to avoid API errors
            valid_texts = [t.strip() for t in texts if t.strip()]
            if not valid_texts:
                return []

            response = client.models.embed_content(
                model=self.model_name,
                contents=valid_texts,
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_DOCUMENT",
                    output_dimensionality=self.dimensions
                )
            )
            
            if response and response.embeddings:
                return [e.values for e in response.embeddings]
            return []
            
        except Exception as e:
            logger.error(f"Batch embedding failed: {str(e)}")
            return []
    
    @staticmethod
    def cosine_similarity(a: List[float], b: List[float]) -> float:
        """
        Calculate the semantic similarity between two vectors.
        Used for ranking medical search results before RAG processing.
        """
        if not a or not b: 
            return 0.0
        try:
            a_arr, b_arr = np.array(a), np.array(b)
            dot_product = np.dot(a_arr, b_arr)
            norm_a = np.linalg.norm(a_arr)
            norm_b = np.linalg.norm(b_arr)
            
            if norm_a == 0 or norm_b == 0:
                return 0.0
                
            return float(dot_product / (norm_a * norm_b))
        except Exception as e:
            logger.error(f"Similarity calculation error: {e}")
            return 0.0

# Singleton instance for use across the FastAPI application
embedding_service = EmbeddingService()