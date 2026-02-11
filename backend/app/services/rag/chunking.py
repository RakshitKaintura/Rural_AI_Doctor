from typing import List, Dict
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.config import settings

class TextChunker:
    def __init__(
        self,
        chunk_size: int = settings.CHUNK_SIZE,
        chunk_overlap: int = settings.CHUNK_OVERLAP
    ):
        """
        Initialize the chunker with Markdown-aware separators for 2026 RAG standards.
        """
        # 2026 Update: We added Markdown specific separators.
        # This ensures that if a medical document has a header like "### Side Effects",
        # the splitter tries to keep that header and its content in one chunk.
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=[
                "\n# ",   # H1 Headers
                "\n## ",  # H2 Headers
                "\n### ", # H3 Headers
                "\n\n",   # Paragraphs
                "\n",     # Lines
                ". ",     # Sentences
                "! ",     # Important warnings
                "? ",     # Clinical questions
                "• ",     # Bullet points
                " ",      # Words
                ""        # Characters
            ]
        )
    
    def chunk_text(self, text: str, metadata: Dict = None) -> List[Dict]:
        """
        Split text into chunks while preserving medical hierarchy and context.
        """
        chunks = self.splitter.split_text(text)
        
        result = []
        for i, chunk in enumerate(chunks):
            chunk_data = {
                "text": chunk,
                "metadata": {
                    **(metadata or {}),
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    # Useful for filtering out 'empty' or tiny noise chunks
                    "char_count": len(chunk) 
                }
            }
            result.append(chunk_data)
        
        return result

    def chunk_documents(self, documents: List[Dict]) -> List[Dict]:
        """
        Processes a list of structured documents for batch ingestion.
        Args:
            documents: List of {"text": str, "metadata": dict}
        """
        all_chunks = []
        for doc in documents:
            text = doc.get("text", "")
            metadata = doc.get("metadata", {})
            
            # Use the internal chunk_text logic to process each doc
            chunks = self.chunk_text(text, metadata)
            all_chunks.extend(chunks)
        
        return all_chunks

# Singleton for application-wide consistency
text_chunker = TextChunker()