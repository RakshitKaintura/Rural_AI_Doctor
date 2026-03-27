import apiClient from './client';

export interface DiagnosisHistory {
  id: number;
  diagnosis: string;
  confidence: number;
  severity: string;
  urgency_level: string;
  created_at: string;
}

export interface UserDashboard {
  total_diagnoses: number;
  recent_diagnoses: DiagnosisHistory[];
  total_chat_sessions: number;
  total_voice_interactions: number;
  total_image_analyses: number;
  last_activity: string | null;
}

export const userAPI = {
  getDashboard: async (): Promise<UserDashboard> => {
    const response = await apiClient.get('/users/dashboard');
    return response.data;
  },

  getHistory: async (skip: number = 0, limit: number = 10): Promise<DiagnosisHistory[]> => {
    const response = await apiClient.get('/users/history/diagnoses', {
      params: { skip, limit },
    });
    return response.data;
  },

  deleteDiagnosis: async (diagnosisId: number) => {
    const response = await apiClient.delete(`/users/history/diagnosis/${diagnosisId}`);
    return response.data;
  },

  downloadPDF: async (diagnosisId: number) => {
    const response = await apiClient.get(`/reports/diagnosis/${diagnosisId}/pdf`, {
      responseType: 'blob',
    });
    
    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `diagnosis_report_${diagnosisId}.pdf`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  },
};