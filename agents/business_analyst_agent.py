import os
import logging
from typing import Dict, Any
from datetime import datetime

from graph.state import ProjectState
from schemas.ba import RequirementsDoc
from db.database import SessionLocal
from db.models import AgentOutput, RunEvent, ProjectRun

logger = logging.getLogger(__name__)

def generate_mock_requirements(prd: Dict[str, Any], requirement: str) -> Dict[str, Any]:
    """
    Generates high-quality mock requirements based on the PRD and requirement.
    """
    req_lower = requirement.lower()
    
    if "task" in req_lower or "todo" in req_lower:
        functional = [
            "The system shall provide a RESTful API for CRUD operations on tasks.",
            "The system shall support updating task state (Pending, In Progress, Completed).",
            "The system shall allow users to filter tasks by tag and priority.",
            "The system shall validate that task titles are non-empty and under 100 characters."
        ]
        non_functional = [
            "The system shall respond to API calls in less than 200ms under standard loads.",
            "The database shall persist task data using SQLite for local development and PostgreSQL for production.",
            "The UI dashboard shall render and be interactive on desktop, tablet, and mobile views."
        ]
        data_flow = [
            "Create Task: Client sends POST /tasks with title/priority -> Backend validates payload -> Database inserts task -> Backend returns 201 with Task JSON.",
            "Get Tasks: Client sends GET /tasks?tag=... -> Backend filters records -> Backend returns JSON list."
        ]
    elif "whatsapp" in req_lower or "chat" in req_lower or "ai" in req_lower:
        functional = [
            "The system shall receive incoming messages via a webhook from WhatsApp API.",
            "The system shall queue message requests to prevent rate-limit failures.",
            "The system shall call an LLM to formulate conversational replies.",
            "The system shall log all messages received and sent with delivery status."
        ]
        non_functional = [
            "The system shall process webhook events and invoke LLM replies within 2 seconds.",
            "The webhook endpoint must support HTTPS and validate WhatsApp hub tokens.",
            "The queue must handle spikes of up to 100 concurrent messages without dropping data."
        ]
        data_flow = [
            "Incoming Webhook: WhatsApp triggers POST /webhook -> Backend validates signature -> Backend queues message -> Backend returns 200 OK.",
            "Processor Loop: Queue workers poll messages -> Worker fetches LLM response -> Worker triggers POST /messages to WhatsApp API -> Database updates delivery status."
        ]
    else:
        functional = [
            "The system shall expose a health check API returning JSON status.",
            "The system shall display a dashboard reflecting application resources.",
            "The system shall maintain user authentication and access controls."
        ]
        non_functional = [
            "The application code shall have at least 80% test coverage.",
            "The configuration settings must be loaded exclusively via environment variables."
        ]
        data_flow = [
            "Health Check: Client sends GET /health -> Backend checks DB/Cache connection -> Backend returns 200 OK status."
        ]

    return {
        "functional_requirements": functional,
        "non_functional_requirements": non_functional,
        "data_flow_notes": data_flow
    }

def ba_node(state: ProjectState) -> Dict[str, Any]:
    """
    Business Analyst Agent Node.
    Analyzes the Product Requirement Document (PRD) and compiles functional/non-functional requirements.
    """
    run_id = state.get("run_id")
    prd = state.get("prd")
    requirement = state.get("business_requirement", "")
    
    if not prd:
        raise ValueError("prd is missing in state. PM node must run first.")

    # Initialize Database Session
    db = SessionLocal()
    
    # Log starting event
    start_event = RunEvent(
        run_id=run_id,
        agent_name="Business Analyst",
        status="STARTED",
        message="BA Agent starting analysis of PRD user stories."
    )
    db.add(start_event)
    db.commit()

    requirements_data = None
    api_key = os.getenv("ANTHROPIC_API_KEY")
    is_mock = not api_key or api_key == "your-anthropic-api-key-here" or api_key.startswith("your-")
    
    if not is_mock:
        try:
            from langchain_anthropic import ChatAnthropic
            
            llm = ChatAnthropic(model="claude-3-5-sonnet-20240620", temperature=0)
            structured_llm = llm.with_structured_output(RequirementsDoc)
            
            prompt = (
                f"You are the Business Analyst Agent.\n"
                f"Create a structured Requirements Document (functional/non-functional/data flows) based on this PRD.\n\n"
                f"PRD details:\n{prd}"
            )
            
            result = structured_llm.invoke(prompt)
            requirements_data = result.dict()
            logger.info("BA Agent generated requirements using Anthropic LLM.")
        except Exception as e:
            logger.error(f"BA Agent LLM call failed. Falling back to mock. Error: {e}")

    if requirements_data is None:
        requirements_data = generate_mock_requirements(prd, requirement)
        logger.info("BA Agent generated requirements using local mock fallback.")

    try:
        # Save output to agent_outputs table
        output_record = AgentOutput(
            run_id=run_id,
            agent_name="Business Analyst",
            artifact_type="requirements_doc",
            content=requirements_data
        )
        db.add(output_record)
        
        # Log completion event
        complete_event = RunEvent(
            run_id=run_id,
            agent_name="Business Analyst",
            status="COMPLETED",
            message="BA Agent completed requirements document. Output successfully persisted."
        )
        db.add(complete_event)
        
        # Update current agent in project_runs
        run_record = db.query(ProjectRun).filter(ProjectRun.id == run_id).first()
        if run_record:
            run_record.current_agent = "Business Analyst"
            
        db.commit()
    except Exception as db_err:
        db.rollback()
        logger.error(f"BA Agent database logging failed: {db_err}")
        raise db_err
    finally:
        db.close()
        
    return {"requirements_doc": requirements_data}
