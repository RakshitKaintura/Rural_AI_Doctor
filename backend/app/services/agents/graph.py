from typing import Literal

from langgraph.graph import END, START, StateGraph

from app.services.agents.state import AgentState


def triage_router(state: AgentState) -> Literal["emergency_action", "image_analysis", "diagnosis"]:
    """Emergency bypass routing after symptom analysis."""
    if state.get("is_emergency"):
        return "emergency_action"
    if state.get("has_image"):
        return "image_analysis"
    return "diagnosis"


def create_medical_agent_graph():
    from app.services.agents.nodes.diagnostician import diagnostician_node
    from app.services.agents.nodes.emergency_action import emergency_action_node
    from app.services.agents.nodes.image_analyzer import image_analyzer_node
    from app.services.agents.nodes.report_generator import report_generator_node
    from app.services.agents.nodes.symptom_analyzer import symptom_analyzer_node
    from app.services.agents.nodes.treatment_planner import treatment_planner_node
    from app.services.agents.nodes.triage import triage_node

    workflow = StateGraph(AgentState)

    workflow.add_node("triage", triage_node)
    workflow.add_node("symptom_analysis", symptom_analyzer_node)
    workflow.add_node("emergency_action", emergency_action_node)
    workflow.add_node("image_analysis", image_analyzer_node)
    workflow.add_node("diagnosis", diagnostician_node)
    workflow.add_node("treatment_planning", treatment_planner_node)
    workflow.add_node("generate_report", report_generator_node)

    workflow.add_edge(START, "triage")
    workflow.add_edge("triage", "symptom_analysis")

    workflow.add_conditional_edges(
        "symptom_analysis",
        triage_router,
        {
            "emergency_action": "emergency_action",
            "image_analysis": "image_analysis",
            "diagnosis": "diagnosis",
        },
    )

    workflow.add_edge("image_analysis", "diagnosis")
    workflow.add_edge("diagnosis", "treatment_planning")
    workflow.add_edge("treatment_planning", "generate_report")
    workflow.add_edge("generate_report", END)
    workflow.add_edge("emergency_action", END)

    return workflow.compile()


_medical_agent_graph = None


def get_medical_agent_graph():
    global _medical_agent_graph
    if _medical_agent_graph is None:
        _medical_agent_graph = create_medical_agent_graph()
    return _medical_agent_graph
