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


def test_full_phase3_pipeline():
    """
    Phase 3 definition of done: given a task manager requirement, the pipeline
    produces a runnable FastAPI backend + React frontend + SQL migrations on disk.
    """
    req = "Build a personal task manager web application"

    # 1. Create run (CEO agent runs, interrupts)
    resp = client.post(f"/runs?requirement={req}")
    assert resp.status_code == 201
    run_id = resp.json()["run_id"]

    # 2. Approve (runs full pipeline: PM → BA → Architect → UX → Frontend + Backend → DB Engineer)
    app_resp = client.post(f"/runs/{run_id}/approve?approved=true")
    assert app_resp.status_code == 200, app_resp.text
    data = app_resp.json()

    assert data["status"] == "COMPLETED"
    assert data["current_agent"] == "Documentation Agent"
    assert "generated_files" in data
    assert len(data["generated_files"]) > 0

    # 3. Verify all DB artifacts are persisted
    db = SessionLocal()
    try:
        artifact_types = {
            r.artifact_type
            for r in db.query(AgentOutput).filter(AgentOutput.run_id == run_id).all()
        }
    finally:
        db.close()

    for expected in ["charter", "prd", "requirements_doc", "architecture_spec",
                     "ux_mockups", "frontend_code", "backend_code", "db_migrations"]:
        assert expected in artifact_types, f"Missing artifact: {expected}"

    # 4. Verify frontend files exist on disk
    frontend_dir = os.path.join("generated_projects", run_id, "frontend")
    assert os.path.isdir(frontend_dir), "Frontend directory not created"

    pkg_json_path = os.path.join(frontend_dir, "package.json")
    assert os.path.isfile(pkg_json_path), "package.json missing"
    with open(pkg_json_path) as f:
        pkg = json.load(f)
    assert "react" in pkg["dependencies"]
    assert "dev" in pkg["scripts"]

    app_jsx_path = os.path.join(frontend_dir, "src", "App.jsx")
    assert os.path.isfile(app_jsx_path), "App.jsx missing"
    with open(app_jsx_path) as f:
        content = f.read()
    assert "export default function App" in content

    # 5. Verify backend files exist on disk
    backend_dir = os.path.join("generated_projects", run_id, "backend")
    assert os.path.isdir(backend_dir), "Backend directory not created"

    main_py_path = os.path.join(backend_dir, "main.py")
    assert os.path.isfile(main_py_path), "main.py missing"
    with open(main_py_path) as f:
        content = f.read()
    assert "FastAPI" in content

    req_txt_path = os.path.join(backend_dir, "requirements.txt")
    assert os.path.isfile(req_txt_path), "requirements.txt missing"
    with open(req_txt_path) as f:
        content = f.read()
    assert "fastapi" in content

    # 6. Verify DB migration files exist on disk
    db_dir = os.path.join("generated_projects", run_id, "db")
    assert os.path.isdir(db_dir), "DB directory not created"

    migration_path = os.path.join(db_dir, "migrations", "001_initial_schema.sql")
    assert os.path.isfile(migration_path), "Migration SQL missing"
    with open(migration_path) as f:
        sql = f.read()
    assert "CREATE TABLE" in sql

    seed_path = os.path.join(db_dir, "seed", "seed_data.sql")
    assert os.path.isfile(seed_path), "Seed SQL missing"

    # 7. Verify /files endpoint
    files_resp = client.get(f"/runs/{run_id}/files")
    assert files_resp.status_code == 200
    files_data = files_resp.json()
    assert files_data["total_files"] > 10  # We generate many files
    file_names = [os.path.basename(f) for f in files_data["files"]]
    assert "package.json" in file_names
    assert "main.py" in file_names
    assert "001_initial_schema.sql" in file_names
