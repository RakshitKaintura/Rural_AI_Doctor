from typing import TypedDict
from langgraph.graph import StateGraph,START,END

class AgentState(TypedDict):
    query: str
    result: str

def router(state:AgentState):
    if "calculate" in state["query"]:
        return "math"
    return "search"

def math(state:AgentState):
    return {"result":"Using math tool"}

def search(state:AgentState):
    return {"result":"Using search tool"}

graph=StateGraph(AgentState)

graph.add_node("math_node",math)
graph.add_node("search_node",search)
graph.add_node("router_node",router)
graph.add_edge(START,"router_node")
graph.add_conditional_edges("router_node",router,{
    "math":"math_node",
    "search":"search_node"
})

graph.add_edge("math_node",END)
graph.add_edge("search_node",END)

workflow=graph.compile()

txt=input("Enter your txt")

print(workflow.invoke({"query":txt}))