import apiClient from './client';
export interface VitalSigns {
  temperature?: number;
  blood_pressure?: string;
  heart_rate?: number;
  oxygen_saturation?: number;
}

export interface Medication {
  name: string;
  dosage: string;
  frequency: string;
  duration: string;
  notes?: string;
}

export interface DiagnosisRequest {
  symptoms: string;
  age?: number;
  gender?: string;
  medical_history?: string;
  vitals?: VitalSigns;
  image_analysis_id?: number;
  patient_id?: number;
}

export interface DiagnosisResponse {
  diagnosis: string; 
  confidence: number;
  differential_diagnoses: string[];
  treatment_plan: {
    immediate_care: string[];
    medications: Medication[];
    non_pharmacological: string[];
    follow_up: {
      timing: string;
      what_to_monitor: string[];
    };
    red_flags: string[];
    when_to_seek_emergency?: string[];
    lifestyle_advice: string[];
    referral_needed: boolean;
    referral_specialty?: string;
    resource_consideration?: string;
  };
  urgency_level: 'EMERGENCY' | 'URGENT' | 'ROUTINE' | 'SELF-CARE';
  final_report: string;
  workflow_steps: string[];
  is_grounded_in_rag: boolean;
}

export const agentsAPI = {

  diagnose: async (request: DiagnosisRequest): Promise<DiagnosisResponse> => {
    const response = await apiClient.post<DiagnosisResponse>('/agents/diagnose', request);
    return response.data;
  },

  simpleDiagnose: async (symptoms: string): Promise<DiagnosisResponse> => {
    const response = await apiClient.post<DiagnosisResponse>('/agents/diagnose/simple', null, {
      params: { symptoms },
    });
    return response.data;
  },

  getHealth: async (): Promise<{ status: string; agents: number }> => {
    const response = await apiClient.get('/agents/health');
    return response.data;
  }
};