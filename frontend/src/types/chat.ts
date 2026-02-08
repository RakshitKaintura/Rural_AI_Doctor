export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
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