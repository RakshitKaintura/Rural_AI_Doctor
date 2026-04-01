from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
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
from app.core.config import settings
from app.db.session import get_db
from app.db.models import ChatHistory, AIDecisionAudit
from datetime import datetime
import uuid

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
   
    try:
       
        session_id = request.session_id or str(uuid.uuid4())
        
     
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
      
        system_prompt = request.system_prompt or MEDICAL_SYSTEM_PROMPT
        response_text = await gemini_client.chat(messages, system_prompt)
        
        if isinstance(response_text, list):
            # Extract text if response_text is a list of dicts (LangChain behavior for some models)
            response_text = "".join([item.get("text", "") for item in response_text if isinstance(item, dict)])
        elif not isinstance(response_text, str):
            response_text = str(response_text)
            
      
        user_msg = ChatHistory(
            session_id=session_id,
            role="user",
            content=messages[-1]["content"] # type: ignore
        )
        db.add(user_msg)
        
        
        assistant_msg = ChatHistory(
            session_id=session_id,
            role="assistant",
            content=response_text
        )
        db.add(assistant_msg)

        audit_record = AIDecisionAudit(
            session_id=session_id,
            source_endpoint="/api/v1/chat/chat",
            decision_type="chat",
            input_summary=messages[-1]["content"],  # type: ignore
            output_summary=response_text[:2000],
            confidence_band="medium",
            model_name=settings.GEMINI_MODEL,
            model_version="v1",
            prompt_version="medical-system-v1",
        )
        db.add(audit_record)
        await db.commit()
        
        return ChatResponse(
            message=response_text,
            session_id=session_id,
            timestamp=datetime.now()
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-symptoms", response_model=SymptomAnalysisResponse)
async def analyze_symptoms(request: SymptomAnalysisRequest, db: AsyncSession = Depends(get_db)):
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

        audit_record = AIDecisionAudit(
            source_endpoint="/api/v1/chat/analyze-symptoms",
            decision_type="symptom_analysis",
            input_summary=request.symptoms,
            output_summary=analysis[:2000] if isinstance(analysis, str) else str(analysis)[:2000],
            confidence_band="medium",
            urgency_level=severity.lower(),
            model_name=settings.GEMINI_MODEL,
            model_version="v1",
            prompt_version="symptom-analysis-v1",
        )
        db.add(audit_record)
        await db.commit()
        
        return SymptomAnalysisResponse(
            analysis=analysis,
            severity=severity,
            possible_conditions=conditions,
            recommendations=triage_result
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


from sqlalchemy.future import select

@router.get("/history/{session_id}")
async def get_chat_history(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    
    result = await db.execute(
        select(ChatHistory)
        .filter(ChatHistory.session_id == session_id)
        .order_by(ChatHistory.created_at)
    )
    history = result.scalars().all()
    
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