from typing import List, Optional
from pydantic import BaseModel, Field
from app.services.agents.state import AgentState
from app.services.llm.gemini_client import gemini_client
from app.services.rag.retriever import vector_retriever
from app.db.session import SessionLocal

class DiagnosisAssessment(BaseModel):
    """Structured schema for clinical diagnosis and reasoning."""
    primary_diagnosis: str = Field(description="The most likely medical condition")
    confidence: float = Field(ge=0, le=1.0, description="Confidence score between 0 and 1")
    differential_diagnoses: List[str] = Field(description="Alternative conditions considered")
    supporting_evidence: List[str] = Field(description="Clinical findings supporting the primary diagnosis")
    ruling_out: List[str] = Field(description="Conditions excluded based on evidence")
    recommended_tests: List[str] = Field(description="Follow-up diagnostic tests needed")
    reasoning: str = Field(description="Detailed clinical justification")

async def diagnostician_node(state: AgentState) -> AgentState:
    """
    Diagnostician: Orchestrates RAG and multimodal evidence to generate a final diagnosis.
    Includes defensive programming to prevent crashes if previous nodes fail.
    """


    analysis = state.get('symptom_analysis') or {}
    vision = state.get('image_analysis') or {}

    primary_symptoms = analysis.get('primary_symptoms', [])
    if not primary_symptoms:
        primary_symptoms = [state.get('symptoms', 'No symptoms provided')]

    context_str = (
        f"Patient Age: {state.get('age', 'Unknown')}\n"
        f"Gender: {state.get('gender', 'Unknown')}\n"
        f"Primary Symptoms: {', '.join(primary_symptoms)}\n"
        f"Duration: {analysis.get('duration', 'N/A')}\n"
        f"Vitals: {state.get('vitals', 'Stable/Not provided')}\n"
    )
    
    if vision:
        context_str += (
            f"\n[Vision Findings]: {', '.join(vision.get('clinical_findings', []))}\n"
            f"[Vision Severity]: {vision.get('severity', 'N/A')}\n"
        )


    query_terms = analysis.get('primary_symptoms', []) + vision.get('clinical_findings', [])
    search_query = " ".join(query_terms) if query_terms else state.get('symptoms', "")

    retrieved_docs = []
    rag_text = "No specific medical guidelines found in local database."
    
    try:
        with SessionLocal() as db:
            retrieved_docs = vector_retriever.search(search_query, db, top_k=3)
            if retrieved_docs:
                rag_text = "\n".join([
                    f"Guideline [{i+1}] (Source: {doc['title']}): {doc['text'][:800]}" 
                    for i, doc in enumerate(retrieved_docs)
                ])
    except Exception as db_err:
        print(f"⚠️ RAG Search Error: {db_err}")
        rag_text = "Knowledge base temporarily unavailable."


    system_prompt = f"""You are a senior clinical diagnostician. 
    Analyze the patient data and local medical guidelines to provide a structured diagnosis.
    
    [PATIENT DATA]
    {context_str}
    
    [MEDICAL GUIDELINES (RAG)]
    {rag_text}
    
    Focus on grounding your diagnosis in the provided guidelines. If the guidelines 
    contradict the symptoms, prioritize clinical safety and list differentials.
    """

    try:
        diagnosis_output: DiagnosisAssessment = await gemini_client.generate_structured(
            prompt=system_prompt,
            response_model=DiagnosisAssessment
        )
    except Exception as llm_err:
        print(f" Diagnostician LLM Error: {llm_err}")
    
        return {
            **state,
            "next_step": "treatment_planning",
            "messages": [{"role": "assistant", "content": "🚨 Diagnosis failed due to LLM error."}]
        }

  
    diag_msg = {
        "role": "assistant",
        "content": (
            f"🔬 **Clinical Diagnosis: {diagnosis_output.primary_diagnosis}**\n"
            f"**Confidence:** {int(diagnosis_output.confidence * 100)}%\n"
            f"**Evidence:** {diagnosis_output.supporting_evidence[0] if diagnosis_output.supporting_evidence else 'Clinical presentation'}\n"
            f"**Recommended Tests:** {', '.join(diagnosis_output.recommended_tests[:2])}"
        )
    }

    print(f"✅ Diagnosis: {diagnosis_output.primary_diagnosis} ({diagnosis_output.confidence})")

    return {
        **state,
        "diagnosis": diagnosis_output.model_dump(),
        "rag_context": retrieved_docs,
        "confidence": diagnosis_output.confidence,
        "next_step": "treatment_planning",
        "messages": [diag_msg]
    }