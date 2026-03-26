from typing import List, Dict, Optional
from pathlib import Path
import docx
from pypdf import PdfReader

class DocumentLoader:
    @staticmethod
    def load_pdf(file_path: str) -> Dict:
        """
        Load PDF with a lightweight extractor first for Render stability.
        """
        try:
            text_parts: List[str] = []
            try:
                reader = PdfReader(file_path)
                for page in reader.pages:
                    extracted = page.extract_text() or ""
                    if extracted.strip():
                        text_parts.append(extracted)
                md_text = "\n\n".join(text_parts)
                extraction_method = "pypdf_text"
            except Exception:
                import pymupdf
                doc = pymupdf.open(file_path)
                md_text = "\n\n".join(page.get_text("text") for page in doc)
                extraction_method = "pymupdf_text"

            if not md_text.strip():
                raise Exception("No extractable text found in PDF")
            
            return {
                "text": md_text,
                "metadata": {
                    "source": Path(file_path).name,
                    "type": "pdf",
                    "extraction_method": extraction_method
                }
            }
        except Exception as e:
            raise Exception(f"Failed to load PDF via PyMuPDF4LLM: {str(e)}")

    @staticmethod
    def load_docx(file_path: str) -> Dict:
        """Load DOCX and extract clean text chunks."""
        try:
            doc = docx.Document(file_path)
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
        
        valid_extensions = {'.pdf', '.docx', '.txt'}
        
        for file_path in directory.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in valid_extensions:
                try:
                    doc = cls.load_document(str(file_path))
                    documents.append(doc)
                except Exception as e:
                    print(f"Error loading {file_path.name}: {e}")
        
        return documents

document_loader = DocumentLoader()