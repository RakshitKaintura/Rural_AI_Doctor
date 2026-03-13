import os
import io
import logging
import tempfile
from google as genai
from typing import Dict, Optional, Any
from pydub import AudioSegment
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import VoiceInteraction
from app.core.config import settings

logger = logging.getLogger(__name__)

class WhisperService:
    def __init__(self):
        """
        Cloud-based transcription service using Gemini 1.5 Flash.
        Saves ~600MB RAM compared to local Whisper models.
        """
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel('gemini-3.0-flash')
        logger.info("🎙️ Cloud Voice Service (Gemini) initialized")

    async def transcribe_audio(self, audio_data: bytes, language: str = None) -> Dict[str, Any]:
        """
        Primary method used by the API endpoints.
        """
        return await self._process_audio_cloud(audio_data, language)

    async def transcribe_and_save(
        self, 
        db: AsyncSession, 
        audio_data: bytes, 
        filename: str,
        session_id: Optional[str] = None,
        patient_id: Optional[int] = None
    ) -> VoiceInteraction:
        """
        Transcribes audio using cloud API and saves result to Supabase.
        """
        try:
            result = await self._process_audio_cloud(audio_data)
            
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
            await db.commit()
            await db.refresh(voice_entry)
            
            return voice_entry
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Voice Service Error: {str(e)}")
            raise e

    async def _process_audio_cloud(self, audio_data: bytes, language: str = None) -> Dict[str, Any]:
        """
        Standardizes audio and sends it to Gemini Cloud for transcription.
        """
        # Create a temporary file with a proper extension for Gemini to recognize
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp_path = tmp.name
        
        try:
            # 1. Standardize audio using pydub
            audio = AudioSegment.from_file(io.BytesIO(audio_data))
            # Convert to mono, 16kHz for optimal transcription
            audio = audio.set_frame_rate(16000).set_channels(1)
            audio.export(tmp_path, format="wav")

            # 2. Upload to Gemini
            # Note: For production, consider file expiration or unique naming
            uploaded_file = genai.upload_file(path=tmp_path, display_name="consultation_audio")
            
            # 3. Generate transcription
            prompt = "Transcribe the following medical audio accurately."
            if language:
                prompt += f" The expected language is {language}."
                
            response = self.model.generate_content([prompt, uploaded_file])
            
            # 4. Clean up the uploaded file from Gemini storage
            genai.delete_file(uploaded_file.name)

            return {
                "text": response.text.strip(),
                "language": language if language else "auto",
                "duration": len(audio) / 1000.0,  # pydub duration is in ms
                "confidence": 0.95  # Gemini doesn't return raw confidence; using a high-quality constant
            }
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

# Singleton initialization
_voice_instance = WhisperService()

def get_whisper_service():
    """
    Factory function for FastAPI dependency injection.
    """
    return _voice_instance

whisper_service = _voice_instance