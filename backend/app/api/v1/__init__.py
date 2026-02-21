from fastapi import APIRouter
from app.api.v1.endpoints import chat, rag, vision, agents

api_router = APIRouter()


api_router.include_router(
    chat.router,    prefix="/chat",   tags=["Clinical Chat"]
)

api_router.include_router(
    rag.router,   prefix="/rag",   tags=["Knowledge Base (RAG)"]
)

api_router.include_router(
    vision.router,  prefix="/vision",  tags=["Medical Imaging"]
)

api_router.include_router(
    agents.router,  prefix="/agents", tags=["Agentic Workflow"]
)
