import os
import uuid
import logging
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager

from db.database import get_db
from db.models import init_db, ProjectRun, AgentOutput, RunEvent
from graph.build_graph import graph
from schemas.ceo import ProjectCharter
from schemas.pm import PRD

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Database Tables
    init_db()
    yield

app = FastAPI(
    title="ASDT API",
    description="API for the Autonomous Software Development Team orchestration platform",
    version="0.1.0",
    lifespan=lifespan
)

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint to verify server is running.
    """
    return {"status": "ok"}

@app.post("/runs", status_code=status.HTTP_201_CREATED)
async def create_run(requirement: str, db: Session = Depends(get_db)):
    """
    Kicks off a new project run. Runs the CEO Agent to produce a Project Charter,
    then interrupts and waits for human approval.
    """
    requirement = requirement.strip()
    if not requirement:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Requirement string cannot be empty."
        )

    # 1. Create a unique run ID
    run_id = str(uuid.uuid4())

    # 2. Create ProjectRun in DB
    run_record = ProjectRun(
        id=run_id,
        business_requirement=requirement,
        status="INITIATED",
        current_agent=None
    )
    db.add(run_record)
    db.commit()

    # 3. Log initial start event
    init_event = RunEvent(
        run_id=run_id,
        agent_name="System",
        status="STARTED",
        message=f"Initialized new project run with ID: {run_id}"
    )
    db.add(init_event)
    db.commit()

    # 4. Invoke LangGraph up to the interrupt point
    config = {"configurable": {"thread_id": run_id}}
    initial_state = {
        "run_id": run_id,
        "business_requirement": requirement,
        "charter": None,
        "prd": None,
        "requirements_doc": None,
        "architecture_spec": None,
        "ux_mockups": None,
        "frontend_code_path": None,
        "backend_code_path": None,
        "db_migrations_path": None,
        "qa_results": None,
        "security_report": None,
        "deployment_manifests": None,
        "api_documentation": None,
        "errors": [],
        "qa_retry_count": 0,
        "security_retry_count": 0
    }

    try:
        # Run graph (will run CEO agent and then pause/interrupt before PM agent)
        graph.invoke(initial_state, config)
    except Exception as e:
        logger.error(f"Error during initial graph execution: {e}")
        run_record.status = "FAILED"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Graph execution failed: {str(e)}"
        )

    # 5. Fetch updated graph state and save checkpoint snapshot to DB
    state_snapshot = graph.get_state(config)
    run_record.state_snapshot = state_snapshot.values
    run_record.status = "AWAITING_APPROVAL"
    run_record.current_agent = "CEO Agent"
    db.commit()

    # 6. Fetch charter from agent_outputs table
    charter_output = db.query(AgentOutput).filter(
        AgentOutput.run_id == run_id,
        AgentOutput.agent_name == "CEO Agent",
        AgentOutput.artifact_type == "charter"
    ).first()

    charter_data = charter_output.content if charter_output else state_snapshot.values.get("charter")

    return {
        "run_id": run_id,
        "status": run_record.status,
        "current_agent": run_record.current_agent,
        "charter": charter_data
    }

@app.get("/runs/{run_id}", status_code=status.HTTP_200_OK)
async def get_run_status(run_id: str, db: Session = Depends(get_db)):
    """
    Retrieves the status, outputs, and event history of a run.
    """
    run_record = db.query(ProjectRun).filter(ProjectRun.id == run_id).first()
    if not run_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run with ID {run_id} not found."
        )

    # Fetch outputs
    outputs = db.query(AgentOutput).filter(AgentOutput.run_id == run_id).all()
    outputs_map = {out.artifact_type: out.content for out in outputs}

    # Fetch events
    events = db.query(RunEvent).filter(RunEvent.run_id == run_id).order_by(RunEvent.timestamp.asc()).all()
    events_list = [
        {
            "agent_name": ev.agent_name,
            "status": ev.status,
            "message": ev.message,
            "timestamp": ev.timestamp.isoformat()
        }
        for ev in events
    ]

    # Fetch generated mockup files on disk if they exist
    mockup_files = []
    mockup_dir = os.path.join("generated_projects", run_id, "mockups")
    if os.path.exists(mockup_dir):
        mockup_files = [
            os.path.join(mockup_dir, f).replace("\\", "/") 
            for f in os.listdir(mockup_dir) 
            if os.path.isfile(os.path.join(mockup_dir, f))
        ]

    return {
        "run_id": run_id,
        "business_requirement": run_record.business_requirement,
        "status": run_record.status,
        "current_agent": run_record.current_agent,
        "outputs": outputs_map,
        "events": events_list,
        "mockup_files": mockup_files
    }

@app.post("/runs/{run_id}/approve", status_code=status.HTTP_200_OK)
async def approve_run_step(run_id: str, approved: bool, db: Session = Depends(get_db)):
    """
    Approves or rejects the project charter.
    If approved, resumes execution to run the Product Manager Agent.
    """
    run_record = db.query(ProjectRun).filter(ProjectRun.id == run_id).first()
    if not run_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run with ID {run_id} not found."
        )

    if run_record.status != "AWAITING_APPROVAL":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Run is not in AWAITING_APPROVAL state. Current status: {run_record.status}"
        )

    if not approved:
        run_record.status = "REJECTED"
        reject_event = RunEvent(
            run_id=run_id,
            agent_name="System",
            status="REJECTED",
            message="Project charter was rejected by human operator."
        )
        db.add(reject_event)
        db.commit()
        return {"status": "REJECTED", "message": "Project run rejected and halted."}

    # 1. Update database status
    run_record.status = "RUNNING"
    approve_event = RunEvent(
        run_id=run_id,
        agent_name="System",
        status="APPROVED",
        message="Project charter approved. Resuming execution to PM Agent."
    )
    db.add(approve_event)
    db.commit()

    # 2. Re-instantiate LangGraph state
    config = {"configurable": {"thread_id": run_id}}
    
    # Restore the state snapshot from database into the checkpointer if memory cleared (e.g. process restarted)
    state_snapshot = graph.get_state(config)
    if not state_snapshot.values and run_record.state_snapshot:
        logger.info("Restoring thread state snapshot from database...")
        graph.update_state(config, run_record.state_snapshot)

    # 3. Resume the graph
    try:
        # Since the CEO node has already run, we pass None to invoke.
        # This will trigger the transition to product_manager agent.
        # The graph will run product_manager, and then try to execute business_analyst, 
        # which raises a NotImplementedError. We catch that expected exception.
        graph.invoke(None, config)
    except NotImplementedError as nie:
        logger.info(f"Graph hit expected stubs downstream: {nie}")
    except Exception as e:
        logger.error(f"Error resuming graph: {e}")
        run_record.status = "FAILED"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Resuming graph failed: {str(e)}"
        )

    # 4. Update the snapshot and status in DB
    final_snapshot = graph.get_state(config)
    run_record.state_snapshot = final_snapshot.values

    # Check for Phase 5 completion (Documentation Agent is the final agent)
    docs_output = db.query(AgentOutput).filter(
        AgentOutput.run_id == run_id,
        AgentOutput.agent_name == "Documentation Agent",
        AgentOutput.artifact_type == "api_documentation"
    ).first()

    # Check for Phase 4 completion (Security Reviewer is the end of Phase 4)
    security_output = db.query(AgentOutput).filter(
        AgentOutput.run_id == run_id,
        AgentOutput.agent_name == "Security Reviewer",
        AgentOutput.artifact_type == "security_report"
    ).first()

    # Check for Phase 3 completion (Database Engineer is the merge point)
    db_output = db.query(AgentOutput).filter(
        AgentOutput.run_id == run_id,
        AgentOutput.agent_name == "Database Engineer",
        AgentOutput.artifact_type == "db_migrations"
    ).first()

    # Fall back to Phase 2 completion (UX Designer)
    mockups_output = db.query(AgentOutput).filter(
        AgentOutput.run_id == run_id,
        AgentOutput.agent_name == "UX Designer",
        AgentOutput.artifact_type == "ux_mockups"
    ).first()

    if docs_output:
        run_record.status = "COMPLETED"
        run_record.current_agent = "Documentation Agent"
        db.commit()

        # Gather all generated files
        project_dir = os.path.join("generated_projects", run_id)
        all_files = _list_files_recursive(project_dir)

        return {
            "run_id": run_id,
            "status": run_record.status,
            "current_agent": run_record.current_agent,
            "generated_files": all_files,
            "api_documentation": docs_output.content
        }
    elif security_output:
        run_record.status = "COMPLETED"
        run_record.current_agent = "Security Reviewer"
        db.commit()

        # Gather all generated project files (including QA/Security reports)
        project_dir = os.path.join("generated_projects", run_id)
        all_files = _list_files_recursive(project_dir)

        return {
            "run_id": run_id,
            "status": run_record.status,
            "current_agent": run_record.current_agent,
            "generated_files": all_files,
            "security_report": security_output.content
        }
    elif db_output:
        run_record.status = "COMPLETED"
        run_record.current_agent = "Database Engineer"
        db.commit()

        # Gather all generated project files
        project_dir = os.path.join("generated_projects", run_id)
        all_files = _list_files_recursive(project_dir)

        return {
            "run_id": run_id,
            "status": run_record.status,
            "current_agent": run_record.current_agent,
            "generated_files": all_files,
            "run_commands": {
                "backend": "cd generated_projects/{run_id}/backend && pip install -r requirements.txt && uvicorn main:app --reload --port 8001",
                "frontend": "cd generated_projects/{run_id}/frontend && npm install && npm run dev",
                "database": "cd generated_projects/{run_id}/db && sqlite3 ../backend/app.db < migrations/001_initial_schema.sql"
            }
        }
    elif mockups_output:
        run_record.status = "COMPLETED"
        run_record.current_agent = "UX Designer"
        db.commit()

        mockup_files = []
        mockup_dir = os.path.join("generated_projects", run_id, "mockups")
        if os.path.exists(mockup_dir):
            mockup_files = _list_files_recursive(mockup_dir)

        return {
            "run_id": run_id,
            "status": run_record.status,
            "current_agent": run_record.current_agent,
            "ux_mockups": mockups_output.content,
            "mockup_files": mockup_files
        }
    else:
        run_record.status = "FAILED"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Graph resumed, but no completion artifact was persisted."
        )


def _list_files_recursive(directory: str):
    """Recursively list all files in a directory, returning forward-slash paths."""
    result = []
    for root, _, files in os.walk(directory):
        for fname in files:
            full = os.path.join(root, fname).replace("\\", "/")
            result.append(full)
    return result


@app.get("/runs/{run_id}/files", status_code=status.HTTP_200_OK)
async def list_run_files(run_id: str, db: Session = Depends(get_db)):
    """
    Lists all files generated on disk for a given run.
    """
    run_record = db.query(ProjectRun).filter(ProjectRun.id == run_id).first()
    if not run_record:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found.")

    project_dir = os.path.join("generated_projects", run_id)
    if not os.path.exists(project_dir):
        return {"run_id": run_id, "files": [], "message": "No files generated yet."}

    files = _list_files_recursive(project_dir)
    return {
        "run_id": run_id,
        "total_files": len(files),
        "files": files
    }
