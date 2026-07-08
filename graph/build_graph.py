from langgraph.graph import StateGraph, END
from .state import ProjectState

# Import agent nodes
from agents.ceo_agent import ceo_node
from agents.product_manager_agent import pm_node
from agents.business_analyst_agent import ba_node
from agents.solution_architect_agent import architect_node
from agents.ux_designer_agent import designer_node
from agents.frontend_developer_agent import frontend_node
from agents.backend_developer_agent import backend_node
from agents.database_engineer_agent import database_node
from agents.qa_engineer_agent import qa_node
from agents.security_reviewer_agent import security_node
from agents.devops_engineer_agent import devops_node
from agents.documentation_agent import documentation_node

def route_after_qa(state: ProjectState) -> str:
    """
    Conditional edge: Route based on QA results.
    If bugs are found and retries are under limit, route back to frontend/backend devs.
    Otherwise, proceed to security check.
    """
    qa_results = state.get("qa_results") or {}
    bugs = qa_results.get("bugs", [])
    retry_count = state.get("qa_retry_count", 0)

    if bugs and retry_count < 3:
        # Loop back to developers (for simplification, return "frontend_developer" 
        # and let the graph activate both or route back)
        return "frontend_developer"
    else:
        return "security_reviewer"

def route_after_security(state: ProjectState) -> str:
    """
    Conditional edge: Route based on security review.
    If vulnerabilities exist, loop back. Otherwise, deploy.
    """
    security_report = state.get("security_report") or {}
    findings = security_report.get("findings", [])
    
    if findings:
        return "backend_developer"
    else:
        return "devops_engineer"

# Build state graph
workflow = StateGraph(ProjectState)

# Add all 12 agent nodes
workflow.add_node("ceo", ceo_node)
workflow.add_node("product_manager", pm_node)
workflow.add_node("business_analyst", ba_node)
workflow.add_node("solution_architect", architect_node)
workflow.add_node("ux_designer", designer_node)
workflow.add_node("frontend_developer", frontend_node)
workflow.add_node("backend_developer", backend_node)
workflow.add_node("database_engineer", database_node)
workflow.add_node("qa_engineer", qa_node)
workflow.add_node("security_reviewer", security_node)
workflow.add_node("devops_engineer", devops_node)
workflow.add_node("documentation_agent", documentation_node)

# Set entry point
workflow.set_entry_point("ceo")

# Define flow
workflow.add_edge("ceo", "product_manager")
workflow.add_edge("product_manager", "business_analyst")
workflow.add_edge("business_analyst", "solution_architect")
workflow.add_edge("solution_architect", "ux_designer")

# Parallel split: Designer -> Frontend & Backend devs
workflow.add_edge("ux_designer", "frontend_developer")
workflow.add_edge("ux_designer", "backend_developer")

# Merge point: Both devs merge into DB Engineer
workflow.add_edge("frontend_developer", "database_engineer")
workflow.add_edge("backend_developer", "database_engineer")

# DB Engineer -> QA
workflow.add_edge("database_engineer", "qa_engineer")

# Conditional edge from QA
workflow.add_conditional_edges(
    "qa_engineer",
    route_after_qa,
    {
        "frontend_developer": "frontend_developer",
        "security_reviewer": "security_reviewer"
    }
)

# Conditional edge from Security
workflow.add_conditional_edges(
    "security_reviewer",
    route_after_security,
    {
        "backend_developer": "backend_developer",
        "devops_engineer": "devops_engineer"
    }
)

# DevOps -> Docs -> End
workflow.add_edge("devops_engineer", "documentation_agent")
workflow.add_edge("documentation_agent", END)

from langgraph.checkpoint.memory import MemorySaver

# Compile graph with checkpointer and interrupt
checkpointer = MemorySaver()
graph = workflow.compile(checkpointer=checkpointer, interrupt_after=["ceo"])
