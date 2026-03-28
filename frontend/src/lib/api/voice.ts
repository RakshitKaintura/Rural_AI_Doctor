import apiClient from './client';

export interface TranscriptionResponse {
  transcription_id: number;
  text: string;
  language: string;
  confidence: number;
  duration_seconds: number;
  session_id: string;
  created_at: string;
}

export interface VoiceDiagnosisResponse {
  transcription: string;
  diagnosis_result: {
    diagnosis: string;
    confidence: number;
    urgency: 'ROUTINE' | 'URGENT' | 'EMERGENCY';
    treatment_summary: string[];
    full_report: string;
  };
  audio_response?: string; // base64 encoded audio
}

export const voiceAPI = {
  /**
   * Send audio to Whisper for STT (Speech-to-Text)
   */
  transcribe: async (
    audioFile: File | Blob,
    language?: string,
    sessionId?: string
  ): Promise<TranscriptionResponse> => {
    const formData = new FormData();
    // Match the backend key: 'file'
    formData.append('file', audioFile, 'recording.wav');
    
    if (language && language !== 'string') formData.append('language', language);
    if (sessionId && sessionId !== 'string') formData.append('session_id', sessionId);

    const response = await apiClient.post('/voice/transcribe', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  /**
   * Convert text to speech (Returns a Blob for direct playback)
   */
  textToSpeech: async (text: string, language: string = 'en', slow: boolean = false): Promise<Blob> => {
    // Note: Backend endpoint is likely /voice/speak based on your previous code
    const response = await apiClient.post(
      '/voice/speak', 
      { text, language, slow },
      { responseType: 'blob' }
    );
    return response.data;
  },

  /**
   * The "Magic" Endpoint: Voice input -> Full Clinical Diagnosis
    * Aligned with backend: async def voice_diagnosis(audio: UploadFile = File(...))
   */
  voiceDiagnosis: async (
    audioFile: File | Blob,
    language: string = 'en',
    age?: number,
    gender?: string,
    medicalHistory?: string
  ): Promise<VoiceDiagnosisResponse> => {
    const formData = new FormData();
    
    // 1. Audio File (Must match backend key: 'audio')
    formData.append('audio', audioFile, 'consultation.webm');
    
    // 2. Language
    formData.append('language', language || 'en');
    
    // 3. Optional Fields - Only append if they have values to avoid 422 errors
    if (age !== undefined && age !== null) {
      formData.append('age', String(age));
    }
    
    if (gender && gender.trim() !== '') {
      formData.append('gender', gender);
    }
    
    if (medicalHistory && medicalHistory.trim() !== '') {
      formData.append('medical_history', medicalHistory);
    }

    // Ensure headers allow multipart form data
    const response = await apiClient.post('/voice/diagnose', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  /**
   * Fetch previous interactions for a patient session
   */
  getHistory: async (sessionId: string): Promise<any> => {
    const response = await apiClient.get(`/voice/history/${sessionId}`);
    return response.data;
  },
};