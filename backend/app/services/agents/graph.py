from typing import Literal
from langgraph.graph import StateGraph, END, START
from app.services.agents.state import AgentState
from app.services.agents.nodes.triage import triage_node
from app.services.agents.nodes.symptom_analyzer import symptom_analyzer_node
from app.services.agents.nodes.image_analyzer import image_analyzer_node
from app.services.agents.nodes.diagnostician import diagnostician_node
from app.services.agents.nodes.treatment_planner import treatment_planner_node
from app.services.agents.nodes.report_generator import report_generator_node


def triage_router(state:AgentState)->Literal["symptom_analysis","image_analysis", "diagnosis"]:
    next_step=state.get('next_step')
    if next_step in ["symptom_analysis", "image_analysis", "diagnosis"]:
        return next_step
    return "symptom_analysis"

def symptom_router(state: AgentState) -> Literal["image_analysis", "diagnosis"]:
    """Routes to image analysis if an image is provided, otherwise proceeds to diagnosis."""
    if state.get('has_image'):
        return "image_analysis"
    return "diagnosis"

def create_medical_agent_graph():
    workflow=StateGraph(AgentState)

    workflow.add_node("triage",triage_node)
    workflow.add_node("symptom_analysis",symptom_analyzer_node)
    workflow.add_node("image_analysis",image_analyzer_node)
    workflow.add_node("diagnosis",diagnostician_node)
    workflow.add_node("treatment_planning", treatment_planner_node)
    workflow.add_node("generate_report", report_generator_node)

    workflow.add_edge(START,"triage")

    workflow.add_conditional_edges(
        "triage",
        triage_router,
        {
            "symptom_analysis": "symptom_analysis",
            "image_analysis": "image_analysis",
            "diagnosis": "diagnosis"
        }
    )

    workflow.add_conditional_edges(
        "symptom_analysis",
        symptom_router,
        {
            "image_analysis": "image_analysis",
            "diagnosis": "diagnosis"
        }
    )

    workflow.add_edge("image_analysis", "diagnosis")
    workflow.add_edge("diagnosis", "treatment_planning")
    workflow.add_edge("treatment_planning", "generate_report")
    workflow.add_edge("generate_report", END)


    compiled_graph=workflow.compile()

    return compiled_graph

medical_agent_graph=create_medical_agent_graph()