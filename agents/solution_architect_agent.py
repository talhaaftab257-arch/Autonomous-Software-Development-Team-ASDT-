import os
import logging
from typing import Dict, Any
from datetime import datetime

from graph.state import ProjectState
from schemas.architect import ArchitectureSpec, ServiceBoundary, DatabaseTable
from db.database import SessionLocal
from db.models import AgentOutput, RunEvent, ProjectRun

logger = logging.getLogger(__name__)

def generate_mock_architecture(requirements: Dict[str, Any], requirement: str) -> Dict[str, Any]:
    """
    Generates a high-quality mock system architecture spec based on the requirements.
    """
    req_lower = requirement.lower()
    
    if "task" in req_lower or "todo" in req_lower:
        diagram = (
            "graph TD\n"
            "    User([User Browser]) -->|HTTP/JSON| FE[React Web App]\n"
            "    FE -->|API Requests| BE[FastAPI Backend]\n"
            "    BE -->|SQLAlchemy ORM| DB[(PostgreSQL Database)]\n"
            "    BE -->|Task Caching| Redis[(Redis Cache)]"
        )
        boundaries = [
            {
                "name": "Frontend Web App",
                "description": "Single Page Application providing the dashboard, task list, filters, and user login templates.",
                "technology": "React, TailwindCSS, Vite"
            },
            {
                "name": "Backend REST API",
                "description": "FastAPI service serving endpoints for task lifecycle management, user authentication, and data exporting.",
                "technology": "FastAPI, Uvicorn, Python"
            },
            {
                "name": "Caching Layer",
                "description": "Redis database handling user session tokens and caching task query lists.",
                "technology": "Redis"
            }
        ]
        db_schema = [
            {
                "table_name": "users",
                "columns": ["id (INTEGER, PK)", "email (VARCHAR(150), UNIQUE)", "password_hash (VARCHAR(256))", "created_at (TIMESTAMP)"],
                "relationships": ["One-to-many relationship with 'tasks' table."]
            },
            {
                "table_name": "tasks",
                "columns": ["id (INTEGER, PK)", "title (VARCHAR(100))", "description (TEXT)", "priority (VARCHAR(10))", "status (VARCHAR(20))", "user_id (INTEGER, FK)", "created_at (TIMESTAMP)"],
                "relationships": ["Foreign key 'user_id' references 'users.id'."]
            },
            {
                "table_name": "tags",
                "columns": ["id (INTEGER, PK)", "name (VARCHAR(50), UNIQUE)"],
                "relationships": ["Many-to-many relationship with 'tasks' through 'task_tags' join table."]
            }
        ]
        choices = {
            "frontend": "React (Vite + CSS)",
            "backend": "FastAPI (Python)",
            "database": "PostgreSQL (SQLite locally)",
            "cache": "Redis",
            "deployment": "Docker Compose"
        }
    elif "whatsapp" in req_lower or "chat" in req_lower or "ai" in req_lower:
        diagram = (
            "graph TD\n"
            "    WA[WhatsApp Cloud API] -->|Webhook HTTP POST| Webhook[FastAPI Webhook Handler]\n"
            "    Webhook -->|Publish Event| Queue[(Redis PubSub)]\n"
            "    Queue -->|Consume Event| Worker[AI Reply Engine]\n"
            "    Worker -->|Query history| DB[(PostgreSQL)]\n"
            "    Worker -->|Invoke LLM| AI[Anthropic API]\n"
            "    Worker -->|Send Reply| WA"
        )
        boundaries = [
            {
                "name": "Webhook Gateway",
                "description": "FastAPI service designed to receive events securely from Meta/WhatsApp Cloud API.",
                "technology": "FastAPI, HTTPS, Verification Hub Token"
            },
            {
                "name": "AI Orchestrator Engine",
                "description": "Worker loop retrieving messages from queue, fetching prompt configurations, calling LLM API, and sending outbound WhatsApp messages.",
                "technology": "LangChain, Python, Redis Celery"
            }
        ]
        db_schema = [
            {
                "table_name": "chats",
                "columns": ["id (INTEGER, PK)", "phone_number (VARCHAR(20))", "session_active (BOOLEAN)", "updated_at (TIMESTAMP)"],
                "relationships": ["One-to-many relationship with 'messages' table."]
            },
            {
                "table_name": "messages",
                "columns": ["id (INTEGER, PK)", "chat_id (INTEGER, FK)", "sender_role (VARCHAR(20))", "message_text (TEXT)", "status (VARCHAR(15))", "timestamp (TIMESTAMP)"],
                "relationships": ["Foreign key 'chat_id' references 'chats.id'."]
            }
        ]
        choices = {
            "frontend": "Not Applicable (WhatsApp interface)",
            "backend": "FastAPI (Python)",
            "database": "PostgreSQL with pgvector",
            "cache_and_queue": "Redis",
            "deployment": "Docker Compose"
        }
    else:
        diagram = (
            "graph TD\n"
            "    Client -->|REST| BE[FastAPI Backend]\n"
            "    BE --> DB[(SQLite)]"
        )
        boundaries = [
            {
                "name": "Core Service API",
                "description": "Handles API routes for resources.",
                "technology": "FastAPI"
            }
        ]
        db_schema = [
            {
                "table_name": "items",
                "columns": ["id (INTEGER, PK)", "name (VARCHAR(50))"],
                "relationships": []
            }
        ]
        choices = {
            "frontend": "None",
            "backend": "FastAPI",
            "database": "SQLite"
        }

    return {
        "mermaid_diagram": diagram,
        "service_boundaries": boundaries,
        "database_schema": db_schema,
        "tech_choices": choices
    }

def architect_node(state: ProjectState) -> Dict[str, Any]:
    """
    Solution Architect Agent Node.
    Analyzes the Requirements Document and compiles a System Architecture Specification.
    """
    run_id = state.get("run_id")
    requirements = state.get("requirements_doc")
    requirement = state.get("business_requirement", "")
    
    if not requirements:
        raise ValueError("requirements_doc is missing in state. BA node must run first.")

    # Initialize Database Session
    db = SessionLocal()
    
    # Log starting event
    start_event = RunEvent(
        run_id=run_id,
        agent_name="Solution Architect",
        status="STARTED",
        message="Architect Agent starting system boundary design."
    )
    db.add(start_event)
    db.commit()

    architecture_data = None
    api_key = os.getenv("ANTHROPIC_API_KEY")
    is_mock = not api_key or api_key == "your-anthropic-api-key-here" or api_key.startswith("your-")
    
    if not is_mock:
        try:
            from langchain_anthropic import ChatAnthropic
            
            llm = ChatAnthropic(model="claude-3-5-sonnet-20240620", temperature=0)
            structured_llm = llm.with_structured_output(ArchitectureSpec)
            
            prompt = (
                f"You are the Solution Architect Agent.\n"
                f"Create a structured Architecture Specification based on these requirements.\n"
                f"Ensure the mermaid_diagram field contains a valid, clean Mermaid diagram code block (like graph TD).\n\n"
                f"Requirements Details:\n{requirements}"
            )
            
            result = structured_llm.invoke(prompt)
            architecture_data = result.dict()
            logger.info("Architect Agent generated system design using Anthropic LLM.")
        except Exception as e:
            logger.error(f"Architect Agent LLM call failed. Falling back to mock. Error: {e}")

    if architecture_data is None:
        architecture_data = generate_mock_architecture(requirements, requirement)
        logger.info("Architect Agent generated system design using local mock fallback.")

    try:
        # Save output to agent_outputs table
        output_record = AgentOutput(
            run_id=run_id,
            agent_name="Solution Architect",
            artifact_type="architecture_spec",
            content=architecture_data
        )
        db.add(output_record)
        
        # Log completion event
        complete_event = RunEvent(
            run_id=run_id,
            agent_name="Solution Architect",
            status="COMPLETED",
            message="Architect Agent completed system design specification. Output successfully persisted."
        )
        db.add(complete_event)
        
        # Update current agent in project_runs
        run_record = db.query(ProjectRun).filter(ProjectRun.id == run_id).first()
        if run_record:
            run_record.current_agent = "Solution Architect"
            
        db.commit()
    except Exception as db_err:
        db.rollback()
        logger.error(f"Architect Agent database logging failed: {db_err}")
        raise db_err
    finally:
        db.close()
        
    return {"architecture_spec": architecture_data}
