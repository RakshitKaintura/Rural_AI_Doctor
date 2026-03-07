from google import genai
from google.genai import types
from app.core.config import settings
from typing import List
import numpy as np
import logging


logger = logging.getLogger(__name__)


client = genai.Client(
    api_key=settings.GOOGLE_API_KEY
)

class EmbeddingService:
    def __init__(self):
       
        self.model_name = "models/text-multilingual-embedding-002" 
        self.dimensions = 768 # Dimensions remain the same, which is convenient

    def _get_embedding(self, text: str, task_type: str) -> List[float]:
        """
        Internal method to fetch embeddings with specific task types.
        """
        try:
            clean_text = text.strip()
            if not clean_text:
                return []

            # Call the Gemini Embedding API
            response = client.models.embed_content(
                model=self.model_name,
                contents=clean_text,
                config=types.EmbedContentConfig(
                    task_type=task_type,
                    output_dimensionality=self.dimensions
                )
            )
            
            # Extract the vector values from the response
            if response and response.embeddings:
                return response.embeddings[0].values
            
            logger.warning(f"Empty embedding returned for model {self.model_name}")
            return []
            
        except Exception as e:
            logger.error(f"Embedding failed for {self.model_name}: {str(e)}")
            return []

    def embed_text(self, text: str) -> List[float]:
        """
        Index medical chunks into the vector database.
        Uses RETRIEVAL_DOCUMENT task type for optimal indexing.
        """
        return self._get_embedding(text, "RETRIEVAL_DOCUMENT")

    def embed_query(self, query: str) -> List[float]:
        """
        Embed user symptoms or search queries.
        Uses RETRIEVAL_QUERY task type to match against indexed documents.
        """
        return self._get_embedding(query, "RETRIEVAL_QUERY")
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Batch process for bulk indexing medical journals or history.
        Reduces API roundtrips significantly.
        """
        try:
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
        Higher value (closer to 1.0) means higher medical relevance.
        """
        if not a or not b: return 0.0
        try:
            a_arr, b_arr = np.array(a), np.array(b)
            norm = np.linalg.norm(a_arr) * np.linalg.norm(b_arr)
            if norm == 0: return 0.0
            return float(np.dot(a_arr, b_arr) / (norm + 1e-10))
        except Exception as e:
            logger.error(f"Similarity calculation error: {e}")
            return 0.0


embedding_service = EmbeddingService()