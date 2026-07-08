import pytest
from fastapi.testclient import TestClient
from api.main import app
from db.database import SessionLocal
from db.models import ProjectRun, AgentOutput, RunEvent, init_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_db():
    """
    Cleans database records before each test.
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
    yield

def test_full_successful_phase1_flow():
    """
    Verifies Phase 1 vertical slice: 
    1. Create a run -> interrupted with charter
    2. Get run status -> verify state
    3. Approve run -> completes with PRD
    4. Get run status again -> verify outputs
    """
    # 1. Create a run
    req_text = "Build a personal task manager web application"
    response = client.post(f"/runs?requirement={req_text}")
    assert response.status_code == 201
    data = response.json()
    
    run_id = data["run_id"]
    assert run_id is not None
    assert data["status"] == "AWAITING_APPROVAL"
    assert data["current_agent"] == "CEO Agent"
    assert "charter" in data
    assert len(data["charter"]["goals"]) > 0
    assert data["charter"]["go_or_no_go"] is True

    # 2. Get run status and verify
    get_resp = client.get(f"/runs/{run_id}")
    assert get_resp.status_code == 200
    get_data = get_resp.json()
    assert get_data["run_id"] == run_id
    assert get_data["status"] == "AWAITING_APPROVAL"
    assert "charter" in get_data["outputs"]
    assert "prd" not in get_data["outputs"]
    assert len(get_data["events"]) > 0

    # 3. Approve run - now runs full pipeline through Phase 3: PM -> BA -> Architect -> UX -> Frontend + Backend -> DB Engineer
    app_resp = client.post(f"/runs/{run_id}/approve?approved=true")
    assert app_resp.status_code == 200
    app_data = app_resp.json()
    assert app_data["run_id"] == run_id
    assert app_data["status"] == "COMPLETED"
    assert app_data["current_agent"] == "Documentation Agent"
    assert "generated_files" in app_data
    assert len(app_data["generated_files"]) > 0

    # 4. Get run status again and check that all outputs are present
    get_resp_final = client.get(f"/runs/{run_id}")
    assert get_resp_final.status_code == 200
    final_data = get_resp_final.json()
    assert final_data["status"] == "COMPLETED"
    assert "charter" in final_data["outputs"]
    assert "prd" in final_data["outputs"]
    assert "requirements_doc" in final_data["outputs"]
    assert "architecture_spec" in final_data["outputs"]
    assert "ux_mockups" in final_data["outputs"]
    assert "frontend_code" in final_data["outputs"]
    assert "backend_code" in final_data["outputs"]
    assert "db_migrations" in final_data["outputs"]
    assert "qa_results" in final_data["outputs"]
    assert "security_report" in final_data["outputs"]
    assert "deployment_manifests" in final_data["outputs"]
    assert "api_documentation" in final_data["outputs"]

def test_rejected_run_flow():
    """
    Verifies that a rejected charter halts the run with REJECTED status.
    """
    # 1. Create a run
    req_text = "Build a simple chat app"
    response = client.post(f"/runs?requirement={req_text}")
    assert response.status_code == 201
    run_id = response.json()["run_id"]

    # 2. Reject run
    app_resp = client.post(f"/runs/{run_id}/approve?approved=false")
    assert app_resp.status_code == 200
    assert app_resp.json()["status"] == "REJECTED"

    # 3. Verify status in DB
    get_resp = client.get(f"/runs/{run_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["status"] == "REJECTED"
    assert "prd" not in get_resp.json()["outputs"]

def test_approve_invalid_status():
    """
    Verifies that attempting to approve a completed or non-awaiting run returns a 400.
    """
    # 1. Create a run and approve it
    req_text = "Build a todo list"
    response = client.post(f"/runs?requirement={req_text}")
    run_id = response.json()["run_id"]
    client.post(f"/runs/{run_id}/approve?approved=true")

    # 2. Try to approve again
    app_resp = client.post(f"/runs/{run_id}/approve?approved=true")
    assert app_resp.status_code == 400
    assert "is not in AWAITING_APPROVAL state" in app_resp.json()["detail"]
