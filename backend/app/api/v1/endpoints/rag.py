from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
import shutil
from pathlib import Path
import tempfile
import logging
import os
import time

from app.db.session import get_db
from app.db.models import MedicalDocument
from app.schemas.rag import (
    DocumentUploadResponse,
    RAGQueryRequest,
    RAGQueryResponse,
    SearchResult
)
from app.services.rag.indexer import document_indexer
from app.services.rag.retriever import vector_retriever
from app.services.llm.gemini_client import gemini_client

logger = logging.getLogger(__name__)
router = APIRouter()

async def background_indexing(file_path: str, db_session: AsyncSession, filename: str):
    try:
        logger.info(f"Starting background indexing for: {filename}")
        chunks = await document_indexer.index_document(
            file_path, 
            db_session, 
            custom_metadata={"uploaded_filename": filename}
        )
        logger.info(f"Background indexing complete for {filename}: {chunks} chunks added.")
    except Exception as e:
        logger.error(f"Background indexing failed for {filename}: {str(e)}")
    finally:
        
        if os.path.exists(file_path):
            for i in range(5): # Try 5 times
                try:
                    os.remove(file_path)
                    logger.debug(f"Successfully deleted temp file: {file_path}")
                    break
                except PermissionError:
                    logger.debug(f"File locked, retrying deletion ({i+1}/5)...")
                    time.sleep(0.5)

@router.get("/stats")
async def get_index_stats(db: AsyncSession = Depends(get_db)):
  
    try:
        total_chunks_result = await db.execute(select(func.count(MedicalDocument.id)))
        total_chunks = total_chunks_result.scalar()
        
        sources_result = await db.execute(
            select(MedicalDocument.metadata_json['uploaded_filename'].astext).distinct()
        )
        sources_query = sources_result.all()
        
        unique_sources = [row[0] for row in sources_query if row[0]]
        
        return {
            "total_chunks": total_chunks or 0,
            "unique_sources": len(unique_sources),
            "sources": unique_sources
        }
    except Exception as e:
        logger.error(f"Stats error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database sync error.")

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...), 
    db: AsyncSession = Depends(get_db)
):
  
    try:
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ['.pdf', '.txt', '.docx']:
             raise HTTPException(status_code=400, detail="Unsupported file format.")

      
        fd, tmp_path = tempfile.mkstemp(suffix=file_ext)
        os.close(fd) 
        
        with open(tmp_path, 'wb') as tmp:
            shutil.copyfileobj(file.file, tmp)
        
        background_tasks.add_task(background_indexing, tmp_path, db, file.filename)
        
        return DocumentUploadResponse(
            message=f"Upload of '{file.filename}' received. Indexing is running in the background.", 
            chunks_indexed=0
        )
    except Exception as e:
        logger.error(f"Upload trigger failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query", response_model=RAGQueryResponse)
@router.post("/search", response_model=RAGQueryResponse) # Alias to fix test 404s
async def rag_query(request: RAGQueryRequest, db: AsyncSession = Depends(get_db)):

    try:
        retrieved_docs = await vector_retriever.search(request.question, db, request.top_k)
        
        if not retrieved_docs:
            return RAGQueryResponse(
                question=request.question, 
                answer="I couldn't find any relevant medical data in the local database.", 
                sources=[]
            )

        context_str = "\n\n".join([f"Source: {d['title']}\n{d['text']}" for d in retrieved_docs])
        
        rag_prompt = f"""
        Use the following clinical context to answer the user's question.
        Context: {context_str}
        
        Question: {request.question}
        
        Clinical Guidance:"""
        
        answer = await gemini_client.generate(rag_prompt)
        
        return RAGQueryResponse(
            question=request.question,
            answer=answer,
            sources=[SearchResult(**d) for d in retrieved_docs] if request.include_sources else []
        )
    except Exception as e:
        logger.error(f"RAG Error: {str(e)}")
        raise HTTPException(status_code=500, detail="AI Generation failed.")