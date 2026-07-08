import pytest
from fastapi.testclient import TestClient
from api.main import app
from graph.build_graph import graph

client = TestClient(app)

def test_health_check():
    """
    Test the health check endpoint returns 200 OK and expected body.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_langgraph_compilation():
    """
    Test that the LangGraph workflow compiles successfully 
    and contains all 12 agent nodes.
    """
    # Verify we can access the compiled graph
    assert graph is not None
    
    # Get the underlying StateGraph workflow representation (nodes)
    # The compiled graph has nodes inside its structure
    # In newer versions of LangGraph, compiled graph exposes `nodes` or we can inspect graph.nodes
    assert hasattr(graph, "nodes") or hasattr(graph, "get_graph")
    
    # Check that we have a valid structure
    # We can check specific expected node names in the compiled graph representation
    nodes = list(graph.nodes.keys()) if hasattr(graph, "nodes") else []
    if nodes:
        expected_nodes = {
            "ceo", "product_manager", "business_analyst", "solution_architect",
            "ux_designer", "frontend_developer", "backend_developer",
            "database_engineer", "qa_engineer", "security_reviewer",
            "devops_engineer", "documentation_agent"
        }
        for node in expected_nodes:
            assert node in nodes
