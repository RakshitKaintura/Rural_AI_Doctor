from fastapi import APIRouter
from app.api.v1.endpoints import chat, vision, agents, voice

api_router = APIRouter()

api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(vision.router, prefix="/vision", tags=["vision"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(voice.router, prefix="/voice", tags=["voice"])