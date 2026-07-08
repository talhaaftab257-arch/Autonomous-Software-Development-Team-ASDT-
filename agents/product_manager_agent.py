import os
import logging
from typing import Dict, Any
from datetime import datetime

from graph.state import ProjectState
from schemas.pm import PRD, UserStory, Feature
from db.database import SessionLocal
from db.models import AgentOutput, RunEvent, ProjectRun

logger = logging.getLogger(__name__)

def generate_mock_prd(charter: Dict[str, Any], requirement: str) -> Dict[str, Any]:
    """
    Generates a high-quality mock PRD based on the project charter and requirement.
    """
    req_lower = requirement.lower()
    
    if "task" in req_lower or "todo" in req_lower:
        user_stories = [
            {
                "role": "As a busy professional",
                "action": "I want to create, read, update, and delete tasks with clear titles and descriptions",
                "benefit": "So that I can stay organized throughout my day.",
                "acceptance_criteria": [
                    "Tasks must have validation preventing blank titles.",
                    "Users must be able to mark tasks as 'completed'."
                ]
            },
            {
                "role": "As an organized user",
                "action": "I want to assign tags and priority levels to tasks",
                "benefit": "So that I can easily group and focus on my most critical items.",
                "acceptance_criteria": [
                    "Priority levels must be selected from a fixed set (High, Medium, Low).",
                    "Tags must be searchable."
                ]
            }
        ]
        features = [
            {
                "name": "Task Dashboard",
                "description": "A single-page view listing all active tasks, grouped by state and priority.",
                "priority": "High",
                "complexity": "Low"
            },
            {
                "name": "Task Management API",
                "description": "CRUD API endpoints inside FastAPI for saving, editing, and deleting tasks.",
                "priority": "High",
                "complexity": "Low"
            },
            {
                "name": "Categorization Tags",
                "description": "Ability to assign arbitrary text labels to tasks for filtering.",
                "priority": "Medium",
                "complexity": "Low"
            }
        ]
    elif "whatsapp" in req_lower or "chat" in req_lower or "ai" in req_lower:
        user_stories = [
            {
                "role": "As a mobile customer",
                "action": "I want to message the support AI assistant on WhatsApp",
                "benefit": "So that I can get instant support without waiting on hold.",
                "acceptance_criteria": [
                    "Messages must receive a reply within 2 seconds.",
                    "If the AI doesn't know the answer, it must offer human escalation."
                ]
            },
            {
                "role": "As a system administrator",
                "action": "I want to inspect message history logs",
                "benefit": "So that I can audit conversation quality and optimize the agent's prompts.",
                "acceptance_criteria": [
                    "Message logs must display timestamps and status (Delivered, Pending, Failed).",
                    "Sensitive customer data must be masked."
                ]
            }
        ]
        features = [
            {
                "name": "WhatsApp Webhook Handler",
                "description": "FastAPI endpoint listening to WhatsApp Cloud API events.",
                "priority": "High",
                "complexity": "Medium"
            },
            {
                "name": "AI Agent Integration",
                "description": "Integration with an LLM to generate intelligent conversational responses.",
                "priority": "High",
                "complexity": "Medium"
            },
            {
                "name": "Conversation Persistence Layer",
                "description": "Database tables mapping phone numbers to conversation threads.",
                "priority": "High",
                "complexity": "Low"
            }
        ]
    else:
        user_stories = [
            {
                "role": "As an end user",
                "action": "I want to navigate through a simple dashboard",
                "benefit": "So that I can inspect system state.",
                "acceptance_criteria": [
                    "Dashboard must load within 500ms.",
                    "All pages must have a consistent header and navigation bar."
                ]
            }
        ]
        features = [
            {
                "name": "Base Dashboard UI",
                "description": "Simple React dashboard containing tables and charts reflecting basic state.",
                "priority": "High",
                "complexity": "Low"
            },
            {
                "name": "Core REST API",
                "description": "FastAPI endpoints returning JSON mock payloads representing resource state.",
                "priority": "High",
                "complexity": "Low"
            }
        ]
        
    return {
        "user_stories": user_stories,
        "prioritized_features": features,
        "acceptance_criteria": [
            "API documentation must auto-generate using Swagger/OpenAPI.",
            "All core endpoints must have associated pytest unit tests.",
            "Application must boot cleanly using docker-compose."
        ]
    }

def pm_node(state: ProjectState) -> Dict[str, Any]:
    """
    Product Manager Agent Node.
    Converts a Project Charter into a Product Requirement Document (PRD).
    """
    run_id = state.get("run_id")
    charter = state.get("charter")
    requirement = state.get("business_requirement", "")
    
    if not charter:
        raise ValueError("charter is missing in state. CEO node must run first.")

    # Initialize Database Session
    db = SessionLocal()
    
    # Log starting event
    start_event = RunEvent(
        run_id=run_id,
        agent_name="Product Manager",
        status="STARTED",
        message="PM Agent starting conversion of Project Charter to PRD."
    )
    db.add(start_event)
    db.commit()

    prd_data = None
    api_key = os.getenv("ANTHROPIC_API_KEY")
    is_mock = not api_key or api_key == "your-anthropic-api-key-here" or api_key.startswith("your-")
    
    if not is_mock:
        try:
            from langchain_anthropic import ChatAnthropic
            
            llm = ChatAnthropic(model="claude-3-5-sonnet-20240620", temperature=0)
            structured_llm = llm.with_structured_output(PRD)
            
            prompt = (
                f"You are the Product Manager Agent.\n"
                f"Create a structured Product Requirement Document (PRD) based on this Project Charter.\n\n"
                f"Business Requirement:\n{requirement}\n\n"
                f"Project Charter:\n{charter}"
            )
            
            result = structured_llm.invoke(prompt)
            prd_data = result.dict()
            logger.info("PM Agent generated PRD using Anthropic LLM.")
        except Exception as e:
            logger.error(f"PM Agent LLM call failed. Falling back to mock. Error: {e}")

    if prd_data is None:
        prd_data = generate_mock_prd(charter, requirement)
        logger.info("PM Agent generated PRD using local mock fallback.")

    try:
        # Save output to agent_outputs table
        output_record = AgentOutput(
            run_id=run_id,
            agent_name="Product Manager",
            artifact_type="prd",
            content=prd_data
        )
        db.add(output_record)
        
        # Log completion event
        complete_event = RunEvent(
            run_id=run_id,
            agent_name="Product Manager",
            status="COMPLETED",
            message="PM Agent completed PRD generation. Output successfully persisted."
        )
        db.add(complete_event)
        
        # Update current agent in project_runs
        run_record = db.query(ProjectRun).filter(ProjectRun.id == run_id).first()
        if run_record:
            run_record.current_agent = "Product Manager"
            
        db.commit()
    except Exception as db_err:
        db.rollback()
        logger.error(f"PM Agent database logging failed: {db_err}")
        raise db_err
    finally:
        db.close()
        
    return {"prd": prd_data}
