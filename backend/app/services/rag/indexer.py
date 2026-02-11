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
        # 1. Load document (Now extracting structured Markdown in 2026)
        doc = document_loader.load_document(file_path)
        
        # 2. Merge custom and extracted metadata
        if custom_metadata:
            doc["metadata"].update(custom_metadata)
        
        # 3. Create Chunks (Markdown-aware in 2026)
        chunks = text_chunker.chunk_text(doc["text"], doc["metadata"])
        
        indexed_count = 0
        
        # 4. Process chunks and prepare for database ingestion
        for chunk in chunks:
            try:
                # Generate embedding (returns List[float])
                # Using the latest 2026 embedding model
                embedding = embedding_service.embed_query(chunk["text"])
                
                # Create database entry
                # Note: metadata_json is the field name used in the model
                med_doc = MedicalDocument(
                    title=f"{doc['metadata']['source']} - Chunk {chunk['metadata']['chunk_index']}",
                    content=chunk["text"],
                    embedding=embedding,
                    metadata_json=chunk["metadata"]
                )
                
                db.add(med_doc)
                indexed_count += 1
                
                # 2026 Batching Optimization: Commit every 50 chunks 
                # to prevent memory bloating during heavy medical library indexing.
                if indexed_count % 50 == 0:
                    db.commit()
            
            except Exception as e:
                # Log error and rollback the failed chunk to keep session healthy
                db.rollback()
                print(f"Error indexing chunk {chunk['metadata']['chunk_index']} of {file_path}: {e}")
                continue
        
        # Final commit for remaining chunks
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
        
        # 2026 Supported extensions
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


# Singleton instance
document_indexer = DocumentIndexer()