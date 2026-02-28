import os
import io
import torch
import whisper
import tempfile
import logging
from typing import Dict, Optional, Any
from pathlib import Path
from pydub import AudioSegment
from sqlalchemy.orm import Session
from app.db.models import VoiceInteraction

logger = logging.getLogger(__name__)

class WhisperService:
    def __init__(self, model_size: str = "base"):
        """
        Initialize Whisper model on CPU/GPU.
        """
        self.model_size = model_size
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        logger.info(f"🎙️ Loading Whisper model ({model_size}) on {self.device}...")
        # fp16=False is required for CPU execution to prevent warnings/errors
        self.model = whisper.load_model(model_size, device=self.device)
        logger.info(f"✅ Whisper model loaded successfully")

    def transcribe_audio(self, audio_data: bytes, language: str = None) -> Dict[str, Any]:
        """
        Primary method used by the API endpoints to get text from raw bytes.
        """
        return self._process_audio(audio_data, language)

    def transcribe_and_save(
        self, 
        db: Session, 
        audio_data: bytes, 
        filename: str,
        session_id: Optional[str] = None,
        patient_id: Optional[int] = None
    ) -> VoiceInteraction:
        """
        Full workflow: Convert -> Transcribe -> Save to DB
        """
        try:
            # 1. Standardize and Transcribe
            result = self._process_audio(audio_data)
            
            # 2. Create Database Record
            voice_entry = VoiceInteraction(
                session_id=session_id,
                patient_id=patient_id,
                audio_filename=filename,
                transcription=result["text"],
                language=result["language"],
                duration_seconds=result["duration"],
                confidence=result["confidence"]
            )
            
            db.add(voice_entry)
            db.commit()
            db.refresh(voice_entry)
            
            return voice_entry
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Voice Service Error: {str(e)}")
            raise e

    def _process_audio(self, audio_data: bytes, language: str = None) -> Dict[str, Any]:
 
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        tmp_path = tmp.name
        
        try:
            # 2. Standardize audio
            audio = AudioSegment.from_file(io.BytesIO(audio_data))
            audio = audio.set_frame_rate(16000).set_channels(1)
            
            # 3. Export and immediately CLOSE the handle so Windows releases the lock
            audio.export(tmp_path, format="wav")
            tmp.close() 

            # 4. Now Whisper can safely open the file
            result = self.model.transcribe(
                tmp_path, 
                language=language,
                fp16=(self.device == "cuda")
            )
            
            return {
                "text": result["text"].strip(),
                "language": result.get("language", "en"),
                "duration": result["segments"][-1]["end"] if result["segments"] else 0,
                "confidence": self._calculate_confidence(result["segments"])
            }
        finally:
            # 5. Manually cleanup once everything is done
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception as e:
                logger.warning(f"Could not remove temp file {tmp_path}: {e}")

    def _calculate_confidence(self, segments: list) -> float:
        """Calculates a rough confidence score based on no_speech probability"""
        if not segments: return 0.0
        # Lower no_speech_prob means higher confidence in the transcription
        return sum(1.0 - s.get('no_speech_prob', 0) for s in segments) / len(segments)

# --- SINGLETON AND FACTORY ---

# Initialize the instance once when the app starts
_whisper_instance = WhisperService(model_size="base")

def get_whisper_service(model_size: str = "base"):
    """
    Factory function used by FastAPI endpoints.
    Returns the initialized singleton.
    """
    global _whisper_instance
    if _whisper_instance is None:
        _whisper_instance = WhisperService(model_size=model_size)
    return _whisper_instance

# Also export the instance directly for convenience
whisper_service = _whisper_instance