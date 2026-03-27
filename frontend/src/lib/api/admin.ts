import apiClient from './client';

export interface AdminStats {
  users: {
    total: number;
    active_30_days: number;
  };
  diagnoses: {
    total: number;
    today: number;
  };
  features: {
    chat_sessions: number;
    voice_interactions: number;
    image_analyses: number;
  };
}

export const adminAPI = {
  getOverview: async (): Promise<AdminStats> => {
    const response = await apiClient.get('/admin/stats/overview');
    return response.data;
  },

  getDiagnosesByDay: async (days: number = 30) => {
    const response = await apiClient.get('/admin/stats/diagnoses-by-day', {
      params: { days },
    });
    return response.data;
  },

  getSeverityDistribution: async () => {
    const response = await apiClient.get('/admin/stats/severity-distribution');
    return response.data;
  },

  getUrgencyDistribution: async () => {
    const response = await apiClient.get('/admin/stats/urgency-distribution');
    return response.data;
  },

  getRecentUsers: async (limit: number = 10) => {
    const response = await apiClient.get('/admin/users/recent', {
      params: { limit },
    });
    return response.data;
  },

  getRecentDiagnoses: async (limit: number = 10) => {
    const response = await apiClient.get('/admin/diagnoses/recent', {
      params: { limit },
    });
    return response.data;
  },
};