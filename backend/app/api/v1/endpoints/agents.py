import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import ImageAnalysis
from app.schemas.agents import DiagnosisRequest, DiagnosisResponse
from app.services.agents.graph import medical_agent_graph
from app.services.agents.state import AgentState

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post(
    "/diagnose", 
    response_model=DiagnosisResponse,
    status_code=status.HTTP_200_OK,
    summary="Run full diagnostic agent workflow",
    description="Trigger a multi-agent pipeline: Triage -> Symptoms -> Vision -> RAG -> Diagnosis -> Plan"
)
async def multi_agent_diagnosis(
    request: DiagnosisRequest,
    db: Session = Depends(get_db)
):
    """
    Executes the clinical LangGraph workflow.
    Fixes the 'AIMessage' object has no attribute 'get' error by using polymorphic message parsing.
    """
    try:
        image_analysis_data = None
        if request.image_analysis_id:
            image_record = db.query(ImageAnalysis).filter(
                ImageAnalysis.id == request.image_analysis_id
            ).first()
            
            if not image_record:
                logger.warning(f"Image ID {request.image_analysis_id} not found. Proceeding without vision data.")
            else:
                image_analysis_data = image_record.analysis_result
        
        initial_state: AgentState = {
            "patient_id": request.patient_id,
            "symptoms": request.symptoms,
            "age": request.age,
            "gender": request.gender,
            "medical_history": request.medical_history,
            "vitals": request.vitals.model_dump() if request.vitals else None,
            "has_image": image_analysis_data is not None,
            "image_type": image_analysis_data.get('image_type') if image_analysis_data else None,
            "image_analysis": image_analysis_data,
            "urgency_level": "ROUTINE",
            "messages": [],
            "confidence": 0.0,
            "triage_result": None,
            "symptom_analysis": None,
            "rag_context": None,
            "diagnosis": None,
            "treatment_plan": None,
            "next_step": None,
            "final_report": None
        }
        
        logger.info(f"🚀 Starting agent workflow for patient: {request.patient_id or 'Guest'}")
        
        final_state = await medical_agent_graph.ainvoke(initial_state)
        
        diagnosis_info = final_state.get('diagnosis') or {}
        treatment_info = final_state.get('treatment_plan') or {}
        
      
        workflow_steps = []
        for msg in final_state.get('messages', []):
 
            if hasattr(msg, "content"):
               
                if hasattr(msg, "type") and msg.type == "ai":
                     workflow_steps.append(msg.content)
                elif "assistant" in str(type(msg)).lower():
                     workflow_steps.append(msg.content)
            
           
            elif isinstance(msg, dict):
                if msg.get('role') == 'assistant':
                    workflow_steps.append(msg.get('content', ''))

        logger.info("✅ Medical workflow completed successfully.")

        return DiagnosisResponse(
            diagnosis=diagnosis_info.get('primary_diagnosis', 'Unable to determine'),
            confidence=final_state.get('confidence', 0.0),
            differential_diagnoses=diagnosis_info.get('differential_diagnoses', []),
            treatment_plan=treatment_info,
            urgency_level=final_state.get('urgency_level', 'ROUTINE'),
            final_report=final_state.get('final_report', 'Report generation failed.'),
            workflow_steps=workflow_steps,
            is_grounded_in_rag=bool(final_state.get('rag_context'))
        )
    
    except Exception as e:
        logger.error(f"❌ Workflow System Failure: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Internal Error: {str(e)}"
        )

@router.get("/health", tags=["System"])
async def get_workflow_health():
    """Endpoint to verify the agent graph is compiled and ready."""
    if medical_agent_graph:
        return {"status": "ready", "engine": "LangGraph 0.2+", "agents": 6}
    return {"status": "error", "message": "Graph not initialized"}