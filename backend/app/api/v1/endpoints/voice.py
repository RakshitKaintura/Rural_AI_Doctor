from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.services.voice.whisper_service import get_whisper_service
import uuid
import base64
import io
import logging
from typing import Optional, Dict, Any

from app.db.session import get_db
from app.db.models import VoiceInteraction
from app.schemas.voice import (
    TranscriptionResponse,
    TTSRequest,
    VoiceDiagnosisResponse
)
from app.services.voice.whisper_service import get_whisper_service
from app.services.voice.tts_service import tts_service
from app.services.voice.audio_utils import audio_utils
from app.services.agents.graph import medical_agent_graph
from app.services.agents.state import AgentState

# Configuration & Logging
logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    language: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Endpoint 1: Audio Transcription only.
    Standardizes audio headers and reduces rural background noise before Whisper processing.
    """
    try:
        # 1. Clean up default Swagger "string" values
        # This prevents Whisper from trying to find a language named "string"
        if language == "string" or not language:
            language = None
        
        if session_id == "string" or not session_id:
            session_id = None

        audio_data = await file.read()
        
        # 2. Validate & Clean (High-pass/Low-pass filters)
        is_valid, error_msg = audio_utils.validate_audio(audio_data)
        if not is_valid:
            # If validation fails, we log it and return a 400
            logger.warning(f"Validation failed for {file.filename}: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
            
        # Preprocess removes DC offset and filters noise (80Hz - 3000Hz)
        clean_audio = audio_utils.preprocess_for_medical_ai(audio_data)
        duration = audio_utils.get_audio_duration(clean_audio)
        
        # 3. Whisper Transcription (Singleton instance)
        whisper = get_whisper_service(model_size="base")
        
        # This call now safely handles the language=None for auto-detection
        result = whisper.transcribe_audio(clean_audio, language=language)
        
        # 4. Persistence
        final_session_id = session_id or str(uuid.uuid4())
        voice_record = VoiceInteraction(
            session_id=final_session_id,
            audio_filename=file.filename,
            transcription=result["text"],
            language=result["language"],
            duration_seconds=duration,
            confidence=result["confidence"]
        )
        
        db.add(voice_record)
        db.commit()
        db.refresh(voice_record)
        
        return voice_record
        
    except HTTPException:
        # Re-raise HTTP exceptions so the correct status code (400) goes to the user
        raise
    except Exception as e:
        logger.error(f"STT Error: {str(e)}")
        # If the error is the WinError 32, it will be caught here
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@router.post("/speak")
async def text_to_speech(request: TTSRequest):
    """
    Endpoint 2: Text-to-Speech Streaming.
    Uses async generators to start audio playback on the client-side immediately.
    """
    try:
        # Returns an AsyncGenerator of bytes
        return StreamingResponse(
            tts_service.stream_speech(request.text, request.language),
            media_type="audio/mpeg",
            headers={"Content-Disposition": "inline; filename=response.mp3"}
        )
    except Exception as e:
        logger.error(f"TTS Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Voice generation failed.")


@router.post("/diagnose", response_model=VoiceDiagnosisResponse)
async def voice_diagnosis(
    audio_file: UploadFile = File(...),
    language: str = Form("en"),
    age: Optional[int] = Form(None),
    gender: Optional[str] = Form(None),
    medical_history: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Endpoint 3: Full End-to-End Workflow.
    Voice Input -> Clean -> Transcribe -> LangGraph Diagnosis -> Audio Summary Output.
    """
    try:
        # 1. Listen (STT)
        audio_data = await audio_file.read()
        clean_audio = audio_utils.preprocess_for_medical_ai(audio_data)
        whisper = get_whisper_service()
        transcription_result = whisper.transcribe_audio(clean_audio, language=language)
        symptoms_text = transcription_result["text"]
        
        # 2. Think (LangGraph Agents)
        # Construct state for the multi-agent system
        initial_state: AgentState = {
            "symptoms": symptoms_text,
            "age": age,
            "gender": gender,
            "medical_history": medical_history,
            "messages": [],
            "urgency_level": "ROUTINE",
            "confidence": 0.0
        }
        
        # Invoke the graph (Diagnosis + Treatment Plan nodes)
        final_state = await medical_agent_graph.ainvoke(initial_state)
        
        # 3. Formulate Speech Response
        diag = final_state.get('diagnosis', {})
        treat = final_state.get('treatment_plan', {})
        
        summary = f"Based on your report, I've identified {diag.get('primary_diagnosis', 'a health concern')}. "
        if final_state.get('urgency_level') == 'EMERGENCY':
            summary = "Emergency Alert: Please contact a hospital immediately. " + summary
            
        # 4. Speak (TTS)
        # Using async TTS to prevent blocking during base64 encoding
        audio_bytes = await tts_service.text_to_speech_async(summary, language=language)
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        return VoiceDiagnosisResponse(
            transcription=symptoms_text,
            diagnosis_result={
                "diagnosis": diag.get('primary_diagnosis', 'Unknown'),
                "confidence": final_state.get('confidence', 0.0),
                "urgency": final_state.get('urgency_level', 'ROUTINE'),
                "treatment_summary": treat.get('immediate_care', []),
                "full_report": final_state.get('final_report', '')
            },
            audio_response=audio_b64,  # Use the renamed field from the schema
            urgency_level=final_state.get('urgency_level', 'ROUTINE')  # Added missing required field
        )
        
    except Exception as e:
        logger.error(f"Full Workflow Error: {e}")
        raise HTTPException(status_code=500, detail="Voice diagnostic process failed.")


@router.get("/history/{session_id}")
async def get_session_audio_history(session_id: str, db: Session = Depends(get_db)):
    """
    Utility: Fetch all voice interactions for a specific session.
    Useful for reviewing patient symptoms over time.
    """
    history = db.query(VoiceInteraction).filter(
        VoiceInteraction.session_id == session_id
    ).order_by(VoiceInteraction.created_at.asc()).all()
    
    return history