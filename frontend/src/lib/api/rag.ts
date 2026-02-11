import axios from 'axios';


export interface IndexStats {
  total_chunks: number;
  unique_sources: number;
  sources: string[];
  last_updated?: string;
}


export interface SearchResult {
  id?: string;
  title: string;
  text: string;
  similarity: number;
  metadata: any;
}

export interface RAGQueryResponse {
  question: string;
  answer: string;
  sources: SearchResult[];
}


const BASE_URL = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, '') || 'http://127.0.0.1:8000/api/v1';

const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000, 
});


export const formatApiError = (error: any): string => {
  if (axios.isAxiosError(error) && error.response?.status === 422) {
    const details = error.response.data.detail;
    if (Array.isArray(details)) {
      return details.map(d => `${d.loc[d.loc.length - 1]}: ${d.msg}`).join(', ');
    }
  }
  return error.message || "An unexpected error occurred";
};

export const ragAPI = {
  getStats: async (): Promise<IndexStats> => {
    try {
      const response = await api.get('/rag/stats');
      return response.data;
    } catch (error) {
      console.error('RAG API Error (getStats):', error);
      throw error;
    }
  },

  uploadFile: async (file: File): Promise<{ message: string; chunks_indexed: number }> => {
    const formData = new FormData();
    formData.append('file', file);
    try {
      const response = await api.post('/rag/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 30000, 
      });
      return response.data;
    } catch (error) {
      console.error('RAG API Error (uploadFile):', error);
      throw error;
    }
  },

  query: async (question: string, topK: number = 5): Promise<RAGQueryResponse> => {
    try {
   
      const response = await api.post('/rag/query', { 
        question: String(question), 
        top_k: Number(topK),
        include_sources: true 
      }, {
        timeout: 45000 
      });
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        console.error('Validation Error Detail:', error.response.data.detail);
      }
      throw error;
    }
  },

  search: async (query: string, topK: number = 5): Promise<SearchResult[]> => {
    try {
      const response = await api.post('/rag/search', { 
        query: String(query), 
        top_k: Number(topK) 
      });
      return response.data.results;
    } catch (error) {
      console.error('RAG API Error (search):', error);
      throw error;
    }
  }
};