export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  metadata?: MessageMetadata;
}

export interface ChatSession {
  id: string;
  messages: Message[];
  createdAt: Date;
}

export type SeverityLevel = 'EMERGENCY' | 'URGENT' | 'ROUTINE' | 'SELF-CARE';

export interface SymptomAnalysis {
  analysis: string;
  severity: SeverityLevel;
  possibleConditions: string[];
  recommendations: string;
}

export interface EmergencyFacility {
  name: string;
  distance_km: number;
  contact_number: string;
  coordinates: {
    lat: number;
    lng: number;
  };
}

export interface MessageMetadata {
  status?: 'CRITICAL' | 'OK';
  red_flags?: string[];
  user_location?: {
    lat: number;
    lng: number;
  };
  nearby_facilities?: EmergencyFacility[];
  first_aid_instructions?: string[];
}
