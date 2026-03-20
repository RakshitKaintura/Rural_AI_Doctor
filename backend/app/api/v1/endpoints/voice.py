"""
Rural AI Doctor - Voice & Audio Endpoints
Handles Transcription (STT), Speech Synthesis (TTS), and Voice Diagnostics.
"""
import uuid
import base64
import logging
from typing import Optional, List

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models import VoiceInteraction
from app.schemas.voice import (
    TranscriptionResponse,
    TTSRequest,
    VoiceDiagnosisResponse
)
from app.services.voice.service import voice_service
from app.services.voice.audio_utils import audio_utils
from app.services.agents.graph import medical_agent_graph
from app.services.agents.state import AgentState

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/languages")
async def get_supported_languages():
  
    langs = voice_service.get_languages()
    return {
        "transcription_languages": langs,
        "tts_languages": langs
    }

@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    file: UploadFile = File(...), # Key matches 'file' in test_transcribe_invalid_file
    language: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
  
    try:
        # Clean Swagger defaults
        clean_lang = None if language in ["string", ""] else language
        
        audio_data = await file.read()
        
        # Validation & Noise reduction
        is_valid, error_msg = audio_utils.validate_audio(audio_data)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
            
        # Transcribe via unified voice_service
        transcription = await voice_service.transcribe_audio(audio_data, language=clean_lang)
        
        # Persistence
        final_session_id = session_id or str(uuid.uuid4())
        voice_record = VoiceInteraction(
            session_id=final_session_id,
            audio_filename=file.filename,
            transcription=transcription,
            language=clean_lang or "auto",
            duration_seconds=audio_utils.get_audio_duration(audio_data),
            confidence=0.9 # Default for placeholder
        )
        
        db.add(voice_record)
        await db.commit()
        await db.refresh(voice_record)
        
        return voice_record
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"STT Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

@router.post("/tts")
@router.post("/speak") 
async def text_to_speech(request: TTSRequest):

    try:
       
        return StreamingResponse(
            voice_service.tts_service.stream_speech(request.text, request.language),
            media_type="audio/mpeg",
            headers={"Content-Disposition": "inline; filename=response.mp3"}
        )
    except Exception as e:
        logger.error(f"TTS Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Voice generation failed.")

@router.post("/diagnose", response_model=VoiceDiagnosisResponse)
async def voice_diagnosis(
    audio: UploadFile = File(...), # Key matches 'audio' in test_voice_diagnose_async
    language: str = Form("en"),
    age: int = Form(...),
    gender: str = Form(...),
    medical_history: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    
    try:
        audio_data = await audio.read()
        symptoms_text = await voice_service.transcribe_audio(audio_data, language=language)
        
        # Orchestrate Agent Graph
        initial_state: AgentState = {
            "symptoms": symptoms_text,
            "age": age,
            "gender": gender,
            "medical_history": medical_history,
            "messages": [],
            "urgency_level": "ROUTINE",
            "confidence": 0.0
        }
        
        final_state = await medical_agent_graph.ainvoke(initial_state)
        
        # Formulate Speech Summary
        diag_name = final_state.get('diagnosis', {}).get('primary_diagnosis', 'a health concern')
        summary = f"Based on your report, I've identified {diag_name}."
        
        if final_state.get('urgency_level') == 'EMERGENCY':
            summary = "Emergency Alert: Contact a hospital immediately. " + summary
            
        # Generate Audio response
        audio_bytes = await voice_service.generate_speech(summary, language=language)
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        return VoiceDiagnosisResponse(
            transcription=symptoms_text,
            diagnosis_result={
                "diagnosis": diag_name,
                "confidence": final_state.get('confidence', 0.0),
                "urgency": final_state.get('urgency_level', 'ROUTINE'),
                "treatment_summary": final_state.get('treatment_plan', {}).get('immediate_care', []),
                "full_report": final_state.get('final_report', '')
            },
            audio_response=audio_b64,
            urgency_level=final_state.get('urgency_level', 'ROUTINE')
        )
        
    except Exception as e:
        logger.error(f"Full Workflow Error: {e}")
        raise HTTPException(status_code=500, detail="Voice diagnostic process failed.")