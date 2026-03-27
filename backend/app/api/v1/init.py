from fastapi import APIRouter
from app.api.v1.endpoints import chat, rag, vision, agents, voice, health, auth, users, reports, admin

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(rag.router, prefix="/rag", tags=["rag"])
api_router.include_router(vision.router, prefix="/vision", tags=["vision"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(voice.router, prefix="/voice", tags=["voice"])