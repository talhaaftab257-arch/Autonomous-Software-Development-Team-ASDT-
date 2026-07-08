import pytest
import os
import json
import shutil
from fastapi.testclient import TestClient
from api.main import app
from db.database import SessionLocal
from db.models import ProjectRun, AgentOutput, RunEvent, init_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_state():
    init_db()
    db = SessionLocal()
    try:
        db.query(AgentOutput).delete()
        db.query(RunEvent).delete()
        db.query(ProjectRun).delete()
        db.commit()
    finally:
        db.close()
    if os.path.exists("generated_projects"):
        shutil.rmtree("generated_projects")
    yield


def test_full_phase4_pipeline():
    """
    Phase 4 definition of done: the pipeline runs through developers,
    database engineer, QA engineer (with loop-back), security reviewer (with loop-back),
    and successfully saves reports.
    """
    req = "Build a personal task manager web application"

    # 1. Create run
    resp = client.post(f"/runs?requirement={req}")
    assert resp.status_code == 201
    run_id = resp.json()["run_id"]

    # 2. Approve (resumes graph through Phase 4)
    app_resp = client.post(f"/runs/{run_id}/approve?approved=true")
    assert app_resp.status_code == 200, app_resp.text
    data = app_resp.json()

    assert data["status"] == "COMPLETED"
    assert data["current_agent"] == "Documentation Agent"
    assert "generated_files" in data
    assert len(data["generated_files"]) > 0

    # 3. Verify all DB artifacts are persisted including qa_results and security_report
    db = SessionLocal()
    try:
        artifacts = {
            r.artifact_type: r.content
            for r in db.query(AgentOutput).filter(AgentOutput.run_id == run_id).all()
        }
        events = db.query(RunEvent).filter(RunEvent.run_id == run_id).all()
    finally:
        db.close()

    for expected in ["charter", "prd", "requirements_doc", "architecture_spec",
                     "ux_mockups", "frontend_code", "backend_code", "db_migrations",
                     "qa_results", "security_report", "deployment_manifests", "api_documentation"]:
        assert expected in artifacts, f"Missing artifact: {expected}"

    # Verify QA results
    qa = artifacts["qa_results"]
    assert qa["overall_status"] == "PASSED"  # The final iteration should pass
    assert qa["total_passed"] == qa["total_tests"]

    # Verify Security report
    sec = artifacts["security_report"]
    assert sec["overall_risk"] == "LOW"  # The final iteration should be secure
    assert len(sec["findings"]) == 0

    # 4. Verify physical files exist on disk
    qa_report_path = os.path.join("generated_projects", run_id, "qa", "report.html")
    sec_report_path = os.path.join("generated_projects", run_id, "security", "report.html")
    assert os.path.isfile(qa_report_path), "QA HTML report not found on disk"
    assert os.path.isfile(sec_report_path), "Security HTML report not found on disk"

    # 5. Check run events timeline for retry loops
    event_agents = [e.agent_name for e in events]
    # Should have multiple QA and Security occurrences due to retry loop
    qa_occurrences = event_agents.count("QA Engineer")
    sec_occurrences = event_agents.count("Security Reviewer")
    
    print(f"QA occurrences: {qa_occurrences}")
    print(f"Security occurrences: {sec_occurrences}")
    
    assert qa_occurrences >= 2, "QA loop back did not trigger"
    assert sec_occurrences >= 2, "Security loop back did not trigger"
