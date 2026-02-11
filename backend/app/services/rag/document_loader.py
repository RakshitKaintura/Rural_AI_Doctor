from typing import List, Dict, Optional
from pathlib import Path
import pymupdf4llm  # 2026 Standard for structure-aware PDF parsing
import docx
from app.core.config import settings

class DocumentLoader:
    @staticmethod
    def load_pdf(file_path: str) -> Dict:
        """
        Load PDF and extract as Markdown to preserve clinical document structure.
        """
        try:
            # 2026 Update: Extracts text while preserving tables and headers as Markdown.
            # This significantly reduces hallucinations during vector search.
            md_text = pymupdf4llm.to_markdown(file_path)
            
            return {
                "text": md_text,
                "metadata": {
                    "source": Path(file_path).name,
                    "type": "pdf",
                    "extraction_method": "pymupdf4llm_markdown"
                }
            }
        except Exception as e:
            raise Exception(f"Failed to load PDF via PyMuPDF4LLM: {str(e)}")

    @staticmethod
    def load_docx(file_path: str) -> Dict:
        """Load DOCX and extract clean text chunks."""
        try:
            doc = docx.Document(file_path)
            
            # 2026 Optimization: Filter out empty paragraphs often found in 
            # medical templates to save on embedding tokens.
            paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
            text = "\n\n".join(paragraphs)
            
            return {
                "text": text,
                "metadata": {
                    "source": Path(file_path).name,
                    "type": "docx",
                    "paragraph_count": len(paragraphs)
                }
            }
        except Exception as e:
            raise Exception(f"Failed to load DOCX: {str(e)}")

    @staticmethod
    def load_txt(file_path: str) -> Dict:
        """Load TXT file with robust UTF-8 handling."""
        try:
            path = Path(file_path)
            # Standardizing on pathlib for all OS compatibility
            text = path.read_text(encoding='utf-8')
            
            return {
                "text": text,
                "metadata": {
                    "source": path.name,
                    "type": "txt"
                }
            }
        except Exception as e:
            raise Exception(f"Failed to load TXT: {str(e)}")

    @classmethod
    def load_document(cls, file_path: str) -> Dict:
        """Auto-detect and load document based on file extension."""
        ext = Path(file_path).suffix.lower()
        
        # Mapping loaders for cleaner 2026-style dispatching
        loaders = {
            '.pdf': cls.load_pdf,
            '.docx': cls.load_docx,
            '.txt': cls.load_txt
        }
        
        if ext not in loaders:
            raise ValueError(f"Unsupported file type: {ext}")
            
        return loaders[ext](file_path)

    @classmethod
    def load_directory(cls, directory_path: str) -> List[Dict]:
        """
        Load all documents from a directory recursively.
        """
        documents = []
        directory = Path(directory_path)
        
        # Supported extensions for the 2026 RAG pipeline
        valid_extensions = {'.pdf', '.docx', '.txt'}
        
        for file_path in directory.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in valid_extensions:
                try:
                    doc = cls.load_document(str(file_path))
                    documents.append(doc)
                except Exception as e:
                    # Logging the error but continuing with other files
                    print(f"Error loading {file_path.name}: {e}")
        
        return documents

# Singleton for application-wide use
document_loader = DocumentLoader()