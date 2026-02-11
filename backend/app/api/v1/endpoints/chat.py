from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    SymptomAnalysisRequest,
    SymptomAnalysisResponse
)
from app.services.llm.gemini_client import gemini_client
from app.services.llm.prompts import (
    MEDICAL_SYSTEM_PROMPT,
    SYMPTOM_ANALYSIS_PROMPT,
    TRIAGE_PROMPT
)
from app.db.session import get_db
from app.db.models import ChatHistory
from datetime import datetime
import uuid

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Medical chat endpoint with conversation history
    """
    try:
       
        session_id = request.session_id or str(uuid.uuid4())
        
     
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
      
        system_prompt = request.system_prompt or MEDICAL_SYSTEM_PROMPT
        response_text = await gemini_client.chat(messages, system_prompt)
        
      
        user_msg = ChatHistory(
            session_id=session_id,
            role="user",
            content=messages[-1]["content"]
        )
        db.add(user_msg)
        
        
        assistant_msg = ChatHistory(
            session_id=session_id,
            role="assistant",
            content=response_text
        )
        db.add(assistant_msg)
        db.commit()
        
        return ChatResponse(
            message=response_text,
            session_id=session_id,
            timestamp=datetime.now()
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-symptoms", response_model=SymptomAnalysisResponse)
async def analyze_symptoms(request: SymptomAnalysisRequest):
    """
    Analyze symptoms and provide preliminary assessment
    """
    try:
      
        prompt = SYMPTOM_ANALYSIS_PROMPT.format(symptoms=request.symptoms)
        
        
        analysis = await gemini_client.generate(prompt)
        
       
        triage_prompt = TRIAGE_PROMPT.format(symptoms=request.symptoms)
        triage_result = await gemini_client.generate(triage_prompt)
        
       
        severity = "ROUTINE"
        if "EMERGENCY" in triage_result.upper():
            severity = "EMERGENCY"
        elif "URGENT" in triage_result.upper():
            severity = "URGENT"
        
      
        conditions = ["Condition analysis in progress"]
        
        return SymptomAnalysisResponse(
            analysis=analysis,
            severity=severity,
            possible_conditions=conditions,
            recommendations=triage_result
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{session_id}")
async def get_chat_history(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve chat history for a session
    """
    history = db.query(ChatHistory).filter(
        ChatHistory.session_id == session_id
    ).order_by(ChatHistory.created_at).all()
    
    return {
        "session_id": session_id,
        "messages": [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.created_at
            }
            for msg in history
        ]
    }