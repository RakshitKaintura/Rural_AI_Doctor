from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func, String
from app.db.session import get_db
from app.db.models import MedicalDocument
from app.schemas.rag import (
    DocumentUploadResponse,
    SearchRequest,
    SearchResponse,
    SearchResult,
    RAGQueryRequest,
    RAGQueryResponse
)
from app.services.rag.indexer import document_indexer
from app.services.rag.retriever import vector_retriever
from app.services.llm.gemini_client import gemini_client
import shutil
from pathlib import Path
import tempfile
import logging
import os

logger = logging.getLogger(__name__)
router = APIRouter()

def background_indexing(file_path: str, db_session: Session, filename: str):
    """
    Worker function to process the document in the background.
    """
    try:
        logger.info(f"Starting background indexing for: {filename}")
        chunks = document_indexer.index_document(
            file_path, 
            db_session, 
            custom_metadata={"uploaded_filename": filename}
        )
        logger.info(f"Background indexing complete for {filename}: {chunks} chunks added.")
    except Exception as e:
        logger.error(f"Background indexing failed for {filename}: {str(e)}")
    finally:
        # Clean up the temporary file after indexing is done
        if os.path.exists(file_path):
            os.unlink(file_path)

@router.get("/stats")
async def get_index_stats(db: Session = Depends(get_db)):
    """
    Optimized stats retrieval using JSONB path navigation.
    """
    try:
        total_chunks = db.query(func.count(MedicalDocument.id)).scalar()
        
     
        sources_query = db.query(
            MedicalDocument.metadata_json['uploaded_filename'].astext
        ).distinct().all()
        
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
    db: Session = Depends(get_db)
):
    """
    Asynchronous upload. Saves file and returns a 202 Accepted status immediately.
    """
    try:
        file_ext = Path(file.filename).suffix.lower()
        
       
        fd, tmp_path = tempfile.mkstemp(suffix=file_ext)
        with os.fdopen(fd, 'wb') as tmp:
            shutil.copyfileobj(file.file, tmp)
        
      
        background_tasks.add_task(background_indexing, tmp_path, db, file.filename)
        
        return DocumentUploadResponse(
            message=f"Upload of '{file.filename}' received. Indexing is running in the background.", 
            chunks_indexed=0  # Chunks will be updated in DB shortly
        )
    except Exception as e:
        logger.error(f"Upload trigger failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query", response_model=RAGQueryResponse)
async def rag_query(request: RAGQueryRequest, db: Session = Depends(get_db)):
    """
    Standard RAG Query using Gemini.
    """
    try:
        retrieved_docs = vector_retriever.search(request.question, db, request.top_k)
        if not retrieved_docs:
            return RAGQueryResponse(
                question=request.question, 
                answer="I couldn't find any relevant medical data. Please ensure guidelines are uploaded.", 
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