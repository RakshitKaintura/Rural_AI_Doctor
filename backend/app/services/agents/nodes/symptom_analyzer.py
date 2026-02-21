"""
Symptom Analyzer Agent - Extracts and structures symptom data
Uses Pydantic Structured Outputs and LangGraph 0.2+ State Management.
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field
from app.services.agents.state import AgentState
from app.services.llm.gemini_client import gemini_client

class SymptomExtraction(BaseModel):
    """Structured schema for medical symptom extraction."""
    primary_symptoms: List[str] = Field(description="The main medical complaints reported by the patient")
    duration: str = Field(description="How long symptoms have been present (e.g., '3 days')")
    severity: Literal["mild", "moderate", "severe", "unknown"]
    associated_symptoms: List[str] = Field(default_factory=list, description="Secondary symptoms mentioned")
    aggravating_factors: List[str] = Field(default_factory=list, description="Things that make the pain or symptom worse")
    relieving_factors: List[str] = Field(default_factory=list, description="Things that provide relief")
    onset: Literal["sudden", "gradual", "unknown"]
    pattern: Literal["constant", "intermittent", "worsening", "improving", "unknown"]

async def symptom_analyzer_node(state: AgentState) -> AgentState:
    """
    Symptom Analyzer: Converts raw text into clinical data points.
    This node is essential for mapping patient lay-language to medical RAG search terms.
    """
    patient_info = (
        f"Raw Symptoms: {state['symptoms']}\n"
        f"Age: {state.get('age', 'Unknown')}\n"
        f"Gender: {state.get('gender', 'Unknown')}"
    )
    
    system_prompt = f"""You are a specialized medical assistant. Your goal is to convert 
    raw patient descriptions into structured clinical data for a doctor's review.
    
    Patient Context:
    {patient_info}
    
    Extract the information precisely. If a specific field is not mentioned by the patient, 
    mark it as 'unknown' or provide an empty list for arrays.
    """

    try:
    
        extracted_data: SymptomExtraction = await gemini_client.generate_structured(
            prompt=system_prompt,
            response_model=SymptomExtraction
        )
    except Exception as e:
        print(f"❌ Symptom Analysis Node Error: {e}")
      
        return {
            **state,
            "next_step": "diagnosis",
            "messages": [{"role": "assistant", "content": "⚠️ Symptom analysis encountered an error. Proceeding with raw data."}]
        }

    
    next_node = "diagnosis"
    if state.get("has_image"):
        next_node = "image_analysis"

    analysis_msg = {
        "role": "assistant",
        "content": (
            f"📋 **Symptom Analysis Complete**\n"
            f"- **Primary:** {', '.join(extracted_data.primary_symptoms) if extracted_data.primary_symptoms else 'None identified'}\n"
            f"- **Duration:** {extracted_data.duration}\n"
            f"- **Severity:** {extracted_data.severity.capitalize()}\n"
            f"- **Onset:** {extracted_data.onset.capitalize()}"
        )
    }

    print(f"✅ Symptom Analysis: {len(extracted_data.primary_symptoms)} symptoms identified")

    return {
        **state,
        "symptom_analysis": extracted_data.model_dump(),
        "next_step": next_node,
        "messages": [analysis_msg] 
    }