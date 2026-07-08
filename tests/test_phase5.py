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


def test_full_phase5_pipeline():
    """
    Phase 5 definition of done: given a task manager requirement, the pipeline
    reaches documentation_agent (completing DevOps + Docs) and saves all artifacts.
    """
    req = "Build a personal task manager web application"

    # 1. Create run
    resp = client.post(f"/runs?requirement={req}")
    assert resp.status_code == 201
    run_id = resp.json()["run_id"]

    # 2. Approve (runs all nodes cleanly to end: PM -> BA -> Architect -> UX -> Frontend + Backend -> DB -> QA -> Sec -> DevOps -> Docs -> END)
    app_resp = client.post(f"/runs/{run_id}/approve?approved=true")
    assert app_resp.status_code == 200, app_resp.text
    data = app_resp.json()

    assert data["status"] == "COMPLETED"
    assert data["current_agent"] == "Documentation Agent"
    assert "api_documentation" in data
    assert "generated_files" in data
    assert len(data["generated_files"]) > 0

    # 3. Verify all 10 Agent Outputs are saved in DB
    db = SessionLocal()
    try:
        artifacts = {
            r.artifact_type
            for r in db.query(AgentOutput).filter(AgentOutput.run_id == run_id).all()
        }
    finally:
        db.close()

    expected_artifacts = [
        "charter", "prd", "requirements_doc", "architecture_spec", "ux_mockups",
        "frontend_code", "backend_code", "db_migrations", "qa_results", "security_report",
        "deployment_manifests", "api_documentation"
    ]
    for expected in expected_artifacts:
        assert expected in artifacts, f"Missing artifact: {expected}"

    # 4. Verify DevOps physical files exist on disk
    devops_dir = os.path.join("generated_projects", run_id, "devops")
    assert os.path.isdir(devops_dir), "DevOps directory not created"
    
    assert os.path.isfile(os.path.join(devops_dir, "backend", "Dockerfile.backend"))
    assert os.path.isfile(os.path.join(devops_dir, "frontend", "Dockerfile.frontend"))
    assert os.path.isfile(os.path.join(devops_dir, "frontend", "nginx.conf"))
    assert os.path.isfile(os.path.join(devops_dir, "docker-compose.yml"))
    assert os.path.isfile(os.path.join(devops_dir, "k8s", "deployment.yaml"))

    # 5. Verify Documentation physical files exist on disk
    docs_dir = os.path.join("generated_projects", run_id, "docs")
    assert os.path.isdir(docs_dir), "Docs directory not created"

    assert os.path.isfile(os.path.join(docs_dir, "README.md"))
    assert os.path.isfile(os.path.join(docs_dir, "docs", "openapi.json"))
    assert os.path.isfile(os.path.join(docs_dir, "docs", "adr", "0001-tech-selection.md"))

    # 6. Verify README content
    with open(os.path.join(docs_dir, "README.md"), encoding="utf-8") as f:
        readme = f.read()
    assert "Tech Stack" in readme
    assert "Local Development Setup" in readme
    assert "Production Deployment" in readme
