import os
import logging
from typing import Dict, Any

from graph.state import ProjectState
from schemas.backend import BackendCode
from db.database import SessionLocal
from db.models import AgentOutput, RunEvent, ProjectRun

logger = logging.getLogger(__name__)


def generate_mock_backend(architecture: Dict, prd: Dict, requirement: str) -> Dict[str, Any]:
    """
    Generates a complete, runnable FastAPI backend project structure.
    """
    req_lower = requirement.lower()
    is_task_app = "task" in req_lower or "todo" in req_lower

    # --- requirements.txt ---
    requirements_txt = """\
fastapi>=0.100.0
uvicorn>=0.22.0
sqlalchemy>=2.0.0
pydantic>=2.0.0
python-dotenv>=1.0.0
"""

    # --- .env.example ---
    env_example = """\
DATABASE_URL=sqlite:///./app.db
SECRET_KEY=your-secret-key-here
DEBUG=True
"""

    # --- database.py ---
    database_py = """\
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
"""

    if is_task_app:
        # --- models.py ---
        models_py = """\
import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from database import Base, engine

class Task(Base):
    __tablename__ = "tasks"
    id          = Column(Integer, primary_key=True, index=True)
    title       = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    priority    = Column(String(10), default="Medium")   # High / Medium / Low
    status      = Column(String(20), default="Pending")  # Pending / In Progress / Completed
    tags        = Column(String(255), nullable=True)      # comma-separated
    created_at  = Column(DateTime, default=datetime.datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)
"""

        # --- routers/tasks.py ---
        tasks_router_py = """\
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from database import get_db
from models import Task, init_db

router = APIRouter(prefix="/tasks", tags=["Tasks"])

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: str = "Medium"
    tags: Optional[List[str]] = []

class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    priority: str
    status: str
    tags: Optional[str]
    model_config = {"from_attributes": True}

@router.get("/", response_model=List[TaskResponse])
def list_tasks(db: Session = Depends(get_db)):
    return db.query(Task).all()

@router.post("/", response_model=TaskResponse, status_code=201)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    if not task.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty.")
    db_task = Task(
        title=task.title,
        description=task.description,
        priority=task.priority,
        tags=",".join(task.tags) if task.tags else None
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@router.put("/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, task: TaskCreate, db: Session = Depends(get_db)):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found.")
    db_task.title       = task.title
    db_task.description = task.description
    db_task.priority    = task.priority
    db_task.tags        = ",".join(task.tags) if task.tags else None
    db.commit()
    db.refresh(db_task)
    return db_task

@router.patch("/{task_id}/complete", response_model=TaskResponse)
def complete_task(task_id: int, db: Session = Depends(get_db)):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found.")
    db_task.status = "Completed"
    db.commit()
    db.refresh(db_task)
    return db_task

@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found.")
    db.delete(db_task)
    db.commit()
"""

        # --- main.py ---
        main_py = """\
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from models import init_db
from routers import tasks

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="TaskFlow API",
    description="Backend API for the TaskFlow task management application. Generated by ASDT.",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks.router)

@app.get("/health")
def health():
    return {"status": "ok", "service": "TaskFlow API"}
"""
        files = [
            {"path": "requirements.txt",     "content": requirements_txt},
            {"path": ".env.example",         "content": env_example},
            {"path": "__init__.py",          "content": ""},
            {"path": "database.py",          "content": database_py},
            {"path": "models.py",            "content": models_py},
            {"path": "main.py",              "content": main_py},
            {"path": "routers/__init__.py",  "content": ""},
            {"path": "routers/tasks.py",     "content": tasks_router_py},
        ]
    else:
        main_py = """\
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

app = FastAPI(title="Generated API", version="0.1.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/items")
def list_items():
    return [{"id": 1, "name": "Sample Item"}]
"""
        files = [
            {"path": "requirements.txt", "content": requirements_txt},
            {"path": ".env.example",     "content": env_example},
            {"path": "database.py",      "content": database_py},
            {"path": "main.py",          "content": main_py},
        ]

    return {
        "files": files,
        "framework": "FastAPI",
        "install_command": "pip install -r requirements.txt",
        "run_command": "uvicorn main:app --reload --port 8001"
    }


def backend_node(state: ProjectState) -> Dict[str, Any]:
    """
    Backend Developer Agent Node.

    Input:
        - architecture_spec (dict): Architecture choices, service boundaries.
        - prd (dict): Acceptance criteria and features.

    Output:
        - backend_code_path (str): Path to generated FastAPI project on disk.

    Failure Mode:
        - Raises ValueError if architecture_spec is missing.
    """
    run_id = state.get("run_id")
    architecture = state.get("architecture_spec")
    prd = state.get("prd") or {}
    requirement = state.get("business_requirement", "")

    if not architecture:
        raise ValueError("architecture_spec is missing. Architect node must run first.")

    db = SessionLocal()
    db.add(RunEvent(run_id=run_id, agent_name="Backend Developer", status="STARTED",
                    message="Backend Developer Agent starting FastAPI project generation."))
    db.commit()

    backend_data = None
    api_key = os.getenv("ANTHROPIC_API_KEY")
    is_mock = not api_key or api_key.startswith("your-")

    if not is_mock:
        try:
            from langchain_anthropic import ChatAnthropic
            llm = ChatAnthropic(model="claude-3-5-sonnet-20240620", temperature=0)
            structured_llm = llm.with_structured_output(BackendCode)
            result = structured_llm.invoke(
                f"You are the Backend Developer Agent. Generate a complete, working FastAPI backend project "
                f"with all files (main.py, models.py, database.py, routers/, requirements.txt) "
                f"based on this architecture and PRD.\n\nArchitecture: {architecture}\nPRD: {prd}"
            )
            backend_data = result.dict()
        except Exception as e:
            logger.error(f"Backend Agent LLM failed, using mock: {e}")

    if backend_data is None:
        backend_data = generate_mock_backend(architecture, prd, requirement)

    # Write files to disk
    output_dir = os.path.join("generated_projects", run_id, "backend")
    for file_info in backend_data["files"]:
        file_path = os.path.join(output_dir, file_info["path"])
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(file_info["content"])

    try:
        db.add(AgentOutput(run_id=run_id, agent_name="Backend Developer",
                           artifact_type="backend_code",
                           content={"path": output_dir,
                                    "files": [f["path"] for f in backend_data["files"]],
                                    "framework": backend_data["framework"],
                                    "install_command": backend_data["install_command"],
                                    "run_command": backend_data["run_command"]}))
        db.add(RunEvent(run_id=run_id, agent_name="Backend Developer", status="COMPLETED",
                        message=f"Generated {len(backend_data['files'])} FastAPI files in {output_dir}"))
        run_rec = db.query(ProjectRun).filter(ProjectRun.id == run_id).first()
        if run_rec:
            run_rec.current_agent = "Backend Developer"
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

    return {"backend_code_path": output_dir}
