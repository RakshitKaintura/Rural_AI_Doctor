from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, List, Any, Literal

class VitalSigns(BaseModel):
    temperature: Optional[float] = Field(None, description="Temperature in Fahrenheit")
    blood_pressure: Optional[str] = Field(None, example="120/80")
    heart_rate: Optional[int] = Field(None, description="Beats per minute")
    oxygen_saturation: Optional[int] = Field(None, ge=0, le=100)

class MedicationSchema(BaseModel):
    name: str
    dosage: str
    frequency: str
    duration: str
    notes: Optional[str] = None

class TreatmentPlanSchema(BaseModel):
    immediate_care: List[str]
    medications: List[MedicationSchema]
    non_pharmacological: List[str]
    follow_up: Dict[str, Any]
    red_flags: List[str]
    referral_needed: bool

class DiagnosisRequest(BaseModel):
    """Input schema for triggering the medical agentic workflow."""
    symptoms: str = Field(..., min_length=5, description="Raw symptoms description from the patient")
    age: Optional[int] = Field(None, ge=0, le=120)
    gender: Optional[str] = Field(None, pattern="^(Male|Female|Other|Prefer not to say)$")
    medical_history: Optional[str] = Field(None)
    vitals: Optional[VitalSigns] = Field(None)
    image_analysis_id: Optional[int] = Field(None, description="Optional link to pre-processed vision analysis")
    patient_id: Optional[int] = Field(None)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "symptoms": "Persistent dry cough and shortness of breath for 3 days",
                "age": 45,
                "gender": "Male",
                "vitals": {"temperature": 101.5, "blood_pressure": "130/85"}
            }
        }
    )


class DiagnosisResponse(BaseModel):
    """Comprehensive output schema representing the final state of the agentic workflow."""
    primary_diagnosis: str = Field(..., alias="diagnosis")
    confidence: float = Field(..., ge=0, le=1.0)
    differential_diagnoses: List[str]
    treatment_plan: TreatmentPlanSchema
    urgency_level: Literal["EMERGENCY", "URGENT", "ROUTINE", "SELF-CARE"]
    final_report: str = Field(..., description="Markdown formatted clinical report")
    
    workflow_steps: List[str] = Field(
        default_factory=list, 
        description="Audit trail of which agents processed this request"
    )
    is_grounded_in_rag: bool = Field(
        default=False, 
        description="Whether clinical guidelines were retrieved from the local knowledge base"
    )

    model_config = ConfigDict(populate_by_name=True)