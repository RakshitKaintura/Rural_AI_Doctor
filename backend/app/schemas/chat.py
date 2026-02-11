from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class ChatMessage(BaseModel):
    role: str  
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    session_id: Optional[str] = None
    system_prompt: Optional[str] = None


class ChatResponse(BaseModel):
    message: str
    session_id: str
    timestamp: datetime


class SymptomAnalysisRequest(BaseModel):
    symptoms: str
    age: Optional[int] = None
    gender: Optional[str] = None


class SymptomAnalysisResponse(BaseModel):
    analysis: str
    severity: str
    possible_conditions: List[str]
    recommendations: str