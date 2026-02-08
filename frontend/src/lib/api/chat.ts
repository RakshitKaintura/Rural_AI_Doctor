import apiClient from './client';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatRequest {
  messages: ChatMessage[];
  session_id?: string;
  system_prompt?: string;
}

export interface ChatResponse {
  message: string;
  session_id: string;
  timestamp: string;
}

export interface SymptomAnalysisRequest {
  symptoms: string;
  age?: number;
  gender?: string;
}

export interface SymptomAnalysisResponse {
  analysis: string;
  severity: string;
  possible_conditions: string[];
  recommendations: string;
}

export const chatAPI = {
  sendMessage: async (request: ChatRequest): Promise<ChatResponse> => {
    const response = await apiClient.post('/chat/chat', request);
    return response.data;
  },

  analyzeSymptoms: async (request: SymptomAnalysisRequest): Promise<SymptomAnalysisResponse> => {
    const response = await apiClient.post('/chat/analyze-symptoms', request);
    return response.data;
  },

  getChatHistory: async (sessionId: string) => {
    const response = await apiClient.get(`/chat/history/${sessionId}`);
    return response.data;
  },
};