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
    
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=[
                "\n# ", 
                "\n## ",  
                "\n### ", 
                "\n\n",   
                "\n",   
                ". ",     
                "! ",     
                "? ",    
                "• ",     
                " ",     
                ""      
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
            
            chunks = self.chunk_text(text, metadata)
            all_chunks.extend(chunks)
        
        return all_chunks

text_chunker = TextChunker()