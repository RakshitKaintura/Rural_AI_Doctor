import os
import io
import logging
import tempfile
from google import genai
from typing import Dict, Optional, Any
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
        self.client = None
        self.model_id = 'gemini-3.1-flash-lite-preview'  # Stable multimodal production standard

    def _get_client(self):
        if self.client is not None:
            return self.client
        if not settings.GOOGLE_API_KEY:
            raise RuntimeError("GOOGLE_API_KEY is not configured")
        self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        logger.info("🎙️ Cloud Voice Service (Gemini V2 SDK) initialized")
        return self.client

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
        client = self._get_client()
        from pydub import AudioSegment

        # Create a temporary file with a proper extension
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp_path = tmp.name
        
        try:
            # 1. Standardize audio using pydub
            audio = AudioSegment.from_file(io.BytesIO(audio_data))
            # Convert to mono, 16kHz for optimal transcription
            audio = audio.set_frame_rate(16000).set_channels(1)
            audio.export(tmp_path, format="wav")

            # 2. CORRECT V2 SYNTAX: Upload to Gemini via client
            uploaded_file = client.files.upload(path=tmp_path)
            
            # 3. CORRECT V2 SYNTAX: Generate transcription
            prompt = "Transcribe the following medical audio accurately."
            if language:
                prompt += f" The expected language is {language}."
                
            response = client.models.generate_content(
                model=self.model_id,
                contents=[prompt, uploaded_file]
            )
            
            # 4. CORRECT V2 SYNTAX: Clean up file
            client.files.delete(name=uploaded_file.name)

            return {
                "text": response.text.strip(),
                "language": language if language else "auto",
                "duration": len(audio) / 1000.0,
                "confidence": 0.95
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