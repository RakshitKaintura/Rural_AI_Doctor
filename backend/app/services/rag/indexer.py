from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.db.models import MedicalDocument
from app.services.rag.document_loader import document_loader
from app.services.rag.chunking import text_chunker
from app.services.rag.embeddings import embedding_service
from pathlib import Path


class DocumentIndexer:
    def index_document(
        self,
        file_path: str,
        db: Session,
        custom_metadata: Optional[dict] = None
    ) -> int:
        """
        Index a single document into the vector database.
        
        Returns:
            Number of chunks successfully indexed.
        """
       
        doc = document_loader.load_document(file_path)
        
       
        if custom_metadata:
            doc["metadata"].update(custom_metadata)
        
        
        chunks = text_chunker.chunk_text(doc["text"], doc["metadata"])
        
        indexed_count = 0
        
       
        for chunk in chunks:
            try:
               
                embedding = embedding_service.embed_query(chunk["text"])
             
                med_doc = MedicalDocument(
                    title=f"{doc['metadata']['source']} - Chunk {chunk['metadata']['chunk_index']}",
                    content=chunk["text"],
                    embedding=embedding,
                    metadata_json=chunk["metadata"]
                )
                
                db.add(med_doc)
                indexed_count += 1
                
           
                if indexed_count % 50 == 0:
                    db.commit()
            
            except Exception as e:
                
                db.rollback()
                print(f"Error indexing chunk {chunk['metadata']['chunk_index']} of {file_path}: {e}")
                continue
        
        db.commit()
        return indexed_count

    def index_directory(
        self,
        directory_path: str,
        db: Session,
        custom_metadata: Optional[dict] = None
    ) -> dict:
        """
        Index all documents in a directory recursively.
        
        Returns:
            Dictionary containing indexing statistics.
        """
        directory = Path(directory_path)
        stats = {
            "total_files": 0,
            "total_chunks": 0,
            "failed": []
        }
        
        valid_extensions = {'.pdf', '.docx', '.txt'}
        
        for file_path in directory.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in valid_extensions:
                try:
                    chunks_indexed = self.index_document(
                        str(file_path),
                        db,
                        custom_metadata
                    )
                    stats["total_files"] += 1
                    stats["total_chunks"] += chunks_indexed
                    print(f"✅ Indexed {file_path.name}: {chunks_indexed} chunks")
                
                except Exception as e:
                    stats["failed"].append({
                        "file": str(file_path),
                        "error": str(e)
                    })
                    print(f"❌ Failed to process {file_path.name}: {e}")
        
        return stats

    def reindex_all(self, db: Session):
        """
        Wipe the current index and prepare for a fresh ingestion.
        """
        try:
            db.query(MedicalDocument).delete()
            db.commit()
            print("✅ Database cleared. Ready for fresh indexing.")
        except Exception as e:
            db.rollback()
            print(f"Error clearing index: {e}")

document_indexer = DocumentIndexer()