from google import genai
from google.genai import types
from app.core.config import settings
from typing import List
import numpy as np
import logging

logger = logging.getLogger(__name__)


client = genai.Client(
    api_key=settings.GOOGLE_API_KEY,
    http_options=types.HttpOptions(api_version="v1beta")
)

class EmbeddingService:
    def __init__(self):
        
        self.model_name = "models/gemini-embedding-004"
        self.dimensions = 768

    def _get_embedding(self, text: str, task_type: str) -> List[float]:
        try:
            clean_text = text.strip()
            if not clean_text:
                return []

            # 2026 embed_content call
            response = client.models.embed_content(
                model=self.model_name,
                contents=clean_text,
                config=types.EmbedContentConfig(
                    task_type=task_type,
                    output_dimensionality=self.dimensions
                )
            )
            
            if response and response.embeddings:
                return response.embeddings[0].values
            return []
            
        except Exception as e:
            logger.error(f"Embedding failed for {self.model_name}: {str(e)}")
            return []

    def embed_text(self, text: str) -> List[float]:
        """Index medical chunks."""
        return self._get_embedding(text, "RETRIEVAL_DOCUMENT")

    def embed_query(self, query: str) -> List[float]:
        """Embed user symptoms/questions."""
        return self._get_embedding(query, "RETRIEVAL_QUERY")
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Batch process for bulk indexing."""
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
            return [e.values for e in response.embeddings]
        except Exception as e:
            logger.error(f"Batch embedding failed: {str(e)}")
            return []
    
    @staticmethod
    def cosine_similarity(a: List[float], b: List[float]) -> float:
        if not a or not b: return 0.0
        a_arr, b_arr = np.array(a), np.array(b)
        norm = np.linalg.norm(a_arr) * np.linalg.norm(b_arr)
        return float(np.dot(a_arr, b_arr) / (norm + 1e-10))

embedding_service = EmbeddingService()