import pytest
import os
import shutil
from fastapi.testclient import TestClient
from api.main import app
from db.database import SessionLocal
from db.models import ProjectRun, AgentOutput, RunEvent, init_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_db_and_files():
    """
    Cleans database records and generated mockup files before each test.
    """
    init_db()
    db = SessionLocal()
    try:
        db.query(AgentOutput).delete()
        db.query(RunEvent).delete()
        db.query(ProjectRun).delete()
        db.commit()
    finally:
        db.close()
        
    # Clean up generated mockup files if directory exists
    if os.path.exists("generated_projects"):
        shutil.rmtree("generated_projects")
        
    yield

def test_full_successful_phase2_flow():
    """
    Verifies Phase 2 planning pipeline:
    1. Create a run -> interrupted with charter
    2. Approve run -> completes running PM, BA, Architect, UX Designer
    3. Verify outputs are in DB (charter, prd, requirements_doc, architecture_spec, ux_mockups)
    4. Verify mockup HTML files are created on disk and listed in the API
    """
    # 1. Create a run
    req_text = "Build a personal task manager web application"
    response = client.post(f"/runs?requirement={req_text}")
    assert response.status_code == 201
    run_id = response.json()["run_id"]
    assert run_id is not None
    assert response.json()["status"] == "AWAITING_APPROVAL"

    # 2. Approve run to trigger full pipeline (PM -> BA -> Architect -> UX Designer)
    app_resp = client.post(f"/runs/{run_id}/approve?approved=true")
    assert app_resp.status_code == 200
    app_data = app_resp.json()
    
    assert app_data["run_id"] == run_id
    assert app_data["status"] == "COMPLETED"
    assert app_data["current_agent"] == "Documentation Agent"
    assert "generated_files" in app_data
    assert len(app_data["generated_files"]) > 0

    # 3. Retrieve final status and check all outputs are persisted
    get_resp = client.get(f"/runs/{run_id}")
    assert get_resp.status_code == 200
    data = get_resp.json()
    
    outputs = data["outputs"]
    assert "charter" in outputs
    assert "prd" in outputs
    assert "requirements_doc" in outputs
    assert "architecture_spec" in outputs
    assert "ux_mockups" in outputs
    assert "frontend_code" in outputs
    assert "backend_code" in outputs
    assert "db_migrations" in outputs
    assert "qa_results" in outputs
    assert "security_report" in outputs
    assert "deployment_manifests" in outputs
    assert "api_documentation" in outputs
    
    # 4. Verify Mermaid diagram content
    architecture = outputs["architecture_spec"]
    assert "mermaid_diagram" in architecture
    assert "graph TD" in architecture["mermaid_diagram"]
    
    # 5. Verify physical mockup HTML files are created on disk
    mockup_files = data["mockup_files"]
    assert len(mockup_files) > 0
    for file_path in mockup_files:
        assert os.path.exists(file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "html" in content.lower()
