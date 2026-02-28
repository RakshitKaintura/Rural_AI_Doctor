from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


from pydantic import  ConfigDict


class TranscriptionResponse(BaseModel):
    # Map 'id' from DB to 'transcription_id'
    id: int 
    # Use 'transcription' to match your DB model
    transcription: str 
    language: str
    confidence: float
    duration_seconds: float
    session_id: str
    created_at: datetime

    # This is the magic line that allows Pydantic to read SQLAlchemy objects
    model_config = ConfigDict(from_attributes=True)


class TTSRequest(BaseModel):
    """Input for the gTTS Service."""
    text: str = Field(..., min_length=1, description="Text to convert to speech")
    language: str = Field("en", description="Language code (en, hi, es, etc.)")
    slow: bool = Field(False, description="Whether to use a slower speaking rate")


class TTSResponse(BaseModel):
    """Output for the gTTS Service."""
    message: str = "Audio generated successfully"
    audio_base64: Optional[str] = None  # Direct playback for small alerts
    audio_url: Optional[str] = None     # Path for larger files (report.mp3)
    language: str
    duration_estimate: float


class VoiceDiagnosisRequest(BaseModel):
    """
    Triggers the full agent pipeline via voice.
    Combines transcription ID with patient metadata.
    """
    transcription_id: int
    language: str = Field("en", description="Preferred language for the audio feedback")
    age: Optional[int] = None
    gender: Optional[str] = None
    medical_history: Optional[str] = None
    vitals: Optional[Dict[str, Any]] = None


class VoiceDiagnosisResponse(BaseModel):
    """The final result of the voice-driven medical assessment."""
    transcription: str
    diagnosis_result: Dict[str, Any]
    audio_response: Optional[str] = None  
    urgency_level: str 