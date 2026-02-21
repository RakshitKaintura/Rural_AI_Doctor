import { CompleteDiagnosis } from '@/components/agents/CompleteDiagnosis';

export default function DiagnosisPage() {
  return (
    <div className="container mx-auto p-6 max-w-5xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Multi-Agent Diagnosis System 🤖</h1>
        <p className="text-gray-600">
          Comprehensive medical assessment using AI agent collaboration
        </p>
      </div>

      <CompleteDiagnosis />
    </div>
  );
}