import asyncio
import logging
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import MedicalDocument
from app.services.rag.document_loader import document_loader
from app.services.rag.chunking import text_chunker
from app.services.rag.embeddings import embedding_service
from pathlib import Path
from app.core.config import settings

logger = logging.getLogger(__name__)


class DocumentIndexer:
    async def index_document(
        self,
        file_path: str,
        db: AsyncSession,
        custom_metadata: Optional[dict] = None
    ) -> int:
        """
        Index a single document into the vector database.
        
        Returns:
            Number of chunks successfully indexed.
        """
        logger.info("Indexing started for file: %s", file_path)
        doc = await asyncio.to_thread(document_loader.load_document, file_path)
        
       
        if custom_metadata:
            doc["metadata"].update(custom_metadata)
        
        
        chunks = await asyncio.to_thread(text_chunker.chunk_text, doc["text"], doc["metadata"])
        logger.info("Extracted %s chunks from %s", len(chunks), file_path)
        if len(chunks) > settings.RAG_MAX_CHUNKS_PER_DOC:
            logger.warning(
                "Chunk count exceeded limit (%s > %s). Truncating for stability.",
                len(chunks),
                settings.RAG_MAX_CHUNKS_PER_DOC,
            )
            chunks = chunks[:settings.RAG_MAX_CHUNKS_PER_DOC]
        
        indexed_count = 0
        failed_count = 0
        
       
        for chunk in chunks:
            try:
                embedding = await asyncio.to_thread(embedding_service.embed_text, chunk["text"])
                if not embedding:
                    failed_count += 1
                    logger.warning(
                        "Skipping chunk %s due to empty/invalid embedding",
                        chunk["metadata"].get("chunk_index"),
                    )
                    continue
             
                med_doc = MedicalDocument(
                    title=f"{doc['metadata']['source']} - Chunk {chunk['metadata']['chunk_index']}",
                    content=chunk["text"],
                    embedding=embedding,
                    metadata_json=chunk["metadata"]
                )
                
                db.add(med_doc)
                indexed_count += 1

                if indexed_count % 50 == 0:
                    await db.commit()
                if indexed_count % 10 == 0:
                    await asyncio.sleep(0)
            
            except Exception as e:
                await db.rollback()
                failed_count += 1
                logger.error(
                    "Error indexing chunk %s of %s: %s",
                    chunk["metadata"].get("chunk_index"),
                    file_path,
                    e,
                )
                continue
        
        await db.commit()
        logger.info(
            "Indexing finished for %s. Inserted: %s, Failed: %s",
            file_path,
            indexed_count,
            failed_count,
        )
        return indexed_count

    async def index_directory(
        self,
        directory_path: str,
        db: AsyncSession,
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
                    chunks_indexed = await self.index_document(
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

    async def reindex_all(self, db: AsyncSession):
        """
        Wipe the current index and prepare for a fresh ingestion.
        """
        from sqlalchemy import delete
        try:
            await db.execute(delete(MedicalDocument))
            await db.commit()
            print("✅ Database cleared. Ready for fresh indexing.")
        except Exception as e:
            await db.rollback()
            print(f"Error clearing index: {e}")

document_indexer = DocumentIndexer()