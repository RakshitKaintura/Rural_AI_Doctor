'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  Loader2, 
  Stethoscope, 
  AlertTriangle,
  CheckCircle,
  FileText,
  Activity
} from 'lucide-react';
import { agentsAPI, DiagnosisResponse } from '@/lib/api/agents';

export function CompleteDiagnosis() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<DiagnosisResponse | null>(null);

  // Form state
  const [symptoms, setSymptoms] = useState('');
  const [age, setAge] = useState('');
  const [gender, setGender] = useState('');
  const [medicalHistory, setMedicalHistory] = useState('');
  const [temperature, setTemperature] = useState('');
  const [heartRate, setHeartRate] = useState('');
  const [bloodPressure, setBloodPressure] = useState('');

  const handleDiagnose = async () => {
    if (!symptoms.trim()) {
      alert('Please describe symptoms');
      return;
    }

    try {
      setLoading(true);

      const vitals: Record<string, any> = {};
      if (temperature) vitals.temperature = parseFloat(temperature);
      if (heartRate) vitals.heart_rate = parseInt(heartRate);
      if (bloodPressure) vitals.blood_pressure = bloodPressure;

      const response = await agentsAPI.diagnose({
        symptoms: symptoms.trim(),
        age: age ? parseInt(age) : undefined,
        gender: gender || undefined,
        medical_history: medicalHistory || undefined,
        vitals: Object.keys(vitals).length > 0 ? vitals : undefined,
      });

      setResult(response);
    } catch (error: any) {
      console.error('Diagnosis error:', error);
      alert(error.response?.data?.detail || 'Diagnosis failed');
    } finally {
      setLoading(false);
    }
  };

  const getUrgencyColor = (urgency: string) => {
    const colors: Record<string, string> = {
      EMERGENCY: 'bg-red-100 text-red-800 border-red-300',
      URGENT: 'bg-orange-100 text-orange-800 border-orange-300',
      ROUTINE: 'bg-green-100 text-green-800 border-green-300',
    };
    return colors[urgency] || 'bg-gray-100 text-gray-800 border-gray-300';
  };

  return (
    <div className="space-y-6">
      {/* Input Form */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Stethoscope className="w-5 h-5" />
          Complete Medical Assessment
        </h3>

        <div className="space-y-4">
          {/* Symptoms */}
          <div>
            <Label htmlFor="symptoms">Symptoms *</Label>
            <Textarea
              id="symptoms"
              placeholder="Describe all symptoms in detail..."
              value={symptoms}
              onChange={(e) => setSymptoms(e.target.value)}
              rows={4}
              disabled={loading}
            />
          </div>

          {/* Patient Info */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="age">Age</Label>
              <Input
                id="age"
                type="number"
                placeholder="e.g., 35"
                value={age}
                onChange={(e) => setAge(e.target.value)}
                disabled={loading}
              />
            </div>
            <div>
              <Label htmlFor="gender">Gender</Label>
              <Input
                id="gender"
                placeholder="e.g., Male/Female"
                value={gender}
                onChange={(e) => setGender(e.target.value)}
                disabled={loading}
              />
            </div>
          </div>

          {/* Vitals */}
          <div className="grid grid-cols-3 gap-4">
            <div>
              <Label htmlFor="temp">Temperature (°F)</Label>
              <Input
                id="temp"
                type="number"
                step="0.1"
                placeholder="98.6"
                value={temperature}
                onChange={(e) => setTemperature(e.target.value)}
                disabled={loading}
              />
            </div>
            <div>
              <Label htmlFor="hr">Heart Rate (bpm)</Label>
              <Input
                id="hr"
                type="number"
                placeholder="72"
                value={heartRate}
                onChange={(e) => setHeartRate(e.target.value)}
                disabled={loading}
              />
            </div>
            <div>
              <Label htmlFor="bp">Blood Pressure</Label>
              <Input
                id="bp"
                placeholder="120/80"
                value={bloodPressure}
                onChange={(e) => setBloodPressure(e.target.value)}
                disabled={loading}
              />
            </div>
          </div>

          {/* Medical History */}
          <div>
            <Label htmlFor="history">Medical History</Label>
            <Textarea
              id="history"
              placeholder="Previous conditions, medications, allergies..."
              value={medicalHistory}
              onChange={(e) => setMedicalHistory(e.target.value)}
              rows={2}
              disabled={loading}
            />
          </div>

          {/* Submit Button */}
          <Button
            onClick={handleDiagnose}
            disabled={loading || !symptoms.trim()}
            className="w-full"
            size="lg"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                Running Multi-Agent Analysis...
              </>
            ) : (
              <>
                <Activity className="w-5 h-5 mr-2" />
                Run Complete Diagnosis
              </>
            )}
          </Button>
        </div>
      </Card>

      {/* Workflow Steps */}
      {loading && (
        <Card className="p-4">
          <h4 className="font-semibold mb-3">Agent Workflow Progress</h4>
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm">
              <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
              <span>Running multi-agent analysis...</span>
            </div>
          </div>
        </Card>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-4">
          {/* Urgency Alert */}
          <Card className={`p-4 border-2 ${getUrgencyColor(result.urgency_level)}`}>
            <div className="flex items-center gap-3">
              {result.urgency_level === 'EMERGENCY' && (
                <AlertTriangle className="w-6 h-6" />
              )}
              {result.urgency_level === 'ROUTINE' && (
                <CheckCircle className="w-6 h-6" />
              )}
              <div>
                <h4 className="font-semibold">
                  Urgency Level: {result.urgency_level}
                </h4>
                {result.urgency_level === 'EMERGENCY' && (
                  <p className="text-sm mt-1">
                    ⚠️ Seek immediate medical attention
                  </p>
                )}
              </div>
            </div>
          </Card>

          {/* Diagnosis */}
          <Card className="p-6">
            <div className="flex items-start justify-between mb-4">
              <h3 className="text-lg font-semibold">Diagnosis</h3>
              <Badge variant="secondary">
                {(result.confidence * 100).toFixed(0)}% Confidence
              </Badge>
            </div>

            <div className="space-y-4">
              <div>
                <h4 className="font-medium mb-2">Primary Diagnosis</h4>
                <p className="text-lg text-gray-900">{result.diagnosis}</p>
              </div>

              {result.differential_diagnoses.length > 0 && (
                <div>
                  <h4 className="font-medium mb-2">Differential Diagnoses</h4>
                  <ul className="space-y-1">
                    {result.differential_diagnoses.map((dx, idx) => (
                      <li key={idx} className="text-sm text-gray-700">
                        • {dx}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </Card>

          {/* Treatment Plan */}
          {result.treatment_plan && (
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Treatment Plan</h3>

              <div className="space-y-4">
                {/* Medications */}
                {result.treatment_plan.medications && result.treatment_plan.medications.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-2">💊 Medications</h4>
                    <div className="space-y-2">
                      {result.treatment_plan.medications.map((med, idx) => (
                        <div key={idx} className="p-3 bg-blue-50 rounded-lg">
                          <p className="font-medium">{med.name}</p>
                          <p className="text-sm text-gray-600">
                            {med.dosage} - {med.frequency} for {med.duration}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Non-Pharmacological */}
                {result.treatment_plan.non_pharmacological && (
                  <div>
                    <h4 className="font-medium mb-2">🏥 General Care</h4>
                    <ul className="space-y-1">
                      {result.treatment_plan.non_pharmacological.map((item, idx) => (
                        <li key={idx} className="text-sm">• {item}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Red Flags */}
                {result.treatment_plan.red_flags && result.treatment_plan.red_flags.length > 0 && (
                  <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                    <h4 className="font-medium text-red-900 mb-2">
                      ⚠️ Warning Signs - Seek Immediate Care If:
                    </h4>
                    <ul className="space-y-1">
                      {result.treatment_plan.red_flags.map((flag, idx) => (
                        <li key={idx} className="text-sm text-red-800">
                          • {flag}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </Card>
          )}

          {/* Final Report */}
          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <FileText className="w-5 h-5" />
                Complete Medical Report
              </h3>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  const blob = new Blob([result.final_report], { type: 'text/plain' });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = 'medical-report.txt';
                  a.click();
                }}
              >
                Download Report
              </Button>
            </div>

            <ScrollArea className="h-96 border rounded-lg p-4 bg-gray-50">
              <pre className="text-sm whitespace-pre-wrap font-mono">
                {result.final_report}
              </pre>
            </ScrollArea>
          </Card>

          {/* Workflow Steps */}
          <details>
            <summary className="cursor-pointer text-sm font-medium text-blue-600 hover:text-blue-700">
              View Agent Workflow Steps
            </summary>
            <Card className="p-4 mt-2">
              <ol className="space-y-2">
                {result.workflow_steps.map((step, idx) => (
                  <li key={idx} className="text-sm flex items-start gap-2">
                    <span className="font-semibold text-gray-500">{idx + 1}.</span>
                    <span>{step}</span>
                  </li>
                ))}
              </ol>
            </Card>
          </details>
        </div>
      )}
    </div>
  );
}