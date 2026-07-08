import os
import logging
from typing import Dict, Any
from datetime import datetime

from graph.state import ProjectState
from schemas.ceo import ProjectCharter
from db.database import SessionLocal
from db.models import AgentOutput, RunEvent, ProjectRun

logger = logging.getLogger(__name__)

def generate_mock_charter(requirement: str) -> Dict[str, Any]:
    """
    Generates a high-quality mock Project Charter based on the business requirement.
    """
    # Simple customization based on requirement keywords
    req_lower = requirement.lower()
    
    if "task" in req_lower or "todo" in req_lower:
        goals = [
            "Create an intuitive dashboard for personal task tracking.",
            "Implement features for task creation, editing, and deletion.",
            "Enable task tagging, priority setting, and categorization."
        ]
        constraints = [
            "Use SQLite for local data storage.",
            "Must be responsive and work seamlessly on mobile and desktop.",
            "Strict adherence to standard FastAPI and React conventions."
        ]
    elif "whatsapp" in req_lower or "chat" in req_lower or "ai" in req_lower:
        goals = [
            "Create a robust AI-powered messaging agent connection framework.",
            "Enable asynchronous message handling and response queuing.",
            "Implement LLM-driven query resolution for incoming user requests."
        ]
        constraints = [
            "Integrate with the official WhatsApp Cloud API.",
            "Response latency must stay under 2 seconds for 95% of queries.",
            "Must maintain secure handling of user conversation histories."
        ]
    else:
        goals = [
            f"Fulfill the core requirements of: '{requirement[:60]}...'.",
            "Establish clean API endpoints with robust error handling.",
            "Ensure a responsive, modern UI design for final system demo."
        ]
        constraints = [
            "Must be containerized using Docker.",
            "Must support SQLite/PostgreSQL as database layer.",
            "Complete core features within standard run iteration limits."
        ]
        
    return {
        "goals": goals,
        "constraints": constraints,
        "success_metrics": [
            "API health check latency under 100ms.",
            "All functional requirements defined in PRD fully implemented.",
            "Zero high-severity security vulnerabilities in static analysis."
        ],
        "go_or_no_go": True,
        "reasoning": f"The business requirement '{requirement[:100]}' is technically feasible, fits the ASDT stack (FastAPI/React), and can be fully completed within a standard project sprint."
    }

def ceo_node(state: ProjectState) -> Dict[str, Any]:
    """
    CEO Agent Node.
    Refines business requirements and produces a Project Charter.
    """
    run_id = state.get("run_id")
    requirement = state.get("business_requirement", "").strip()
    
    if not requirement:
        raise ValueError("business_requirement is missing or empty in state.")

    # Initialize Database Session
    db = SessionLocal()
    
    # Log starting event
    start_event = RunEvent(
        run_id=run_id,
        agent_name="CEO Agent",
        status="STARTED",
        message="CEO Agent starting analysis of business requirements."
    )
    db.add(start_event)
    db.commit()

    charter_data = None
    api_key = os.getenv("ANTHROPIC_API_KEY")
    is_mock = not api_key or api_key == "your-anthropic-api-key-here" or api_key.startswith("your-")
    
    if not is_mock:
        try:
            from langchain_anthropic import ChatAnthropic
            
            llm = ChatAnthropic(model="claude-3-5-sonnet-20240620", temperature=0)
            structured_llm = llm.with_structured_output(ProjectCharter)
            
            prompt = (
                f"You are the CEO Agent for a software project.\n"
                f"Analyze the following business requirement and produce a structured Project Charter.\n\n"
                f"Business Requirement:\n{requirement}"
            )
            
            result = structured_llm.invoke(prompt)
            charter_data = result.dict()
            logger.info("CEO Agent generated charter using Anthropic LLM.")
        except Exception as e:
            logger.error(f"CEO Agent LLM call failed. Falling back to mock data. Error: {e}")
            
    if charter_data is None:
        charter_data = generate_mock_charter(requirement)
        logger.info("CEO Agent generated charter using local mock fallback.")

    try:
        # Save output to agent_outputs table
        output_record = AgentOutput(
            run_id=run_id,
            agent_name="CEO Agent",
            artifact_type="charter",
            content=charter_data
        )
        db.add(output_record)
        
        # Log completion event
        complete_event = RunEvent(
            run_id=run_id,
            agent_name="CEO Agent",
            status="COMPLETED",
            message="CEO Agent completed analysis. Project Charter successfully generated."
        )
        db.add(complete_event)
        
        # Update current agent in project_runs
        run_record = db.query(ProjectRun).filter(ProjectRun.id == run_id).first()
        if run_record:
            run_record.current_agent = "CEO Agent"
            
        db.commit()
    except Exception as db_err:
        db.rollback()
        logger.error(f"CEO Agent database logging failed: {db_err}")
        raise db_err
    finally:
        db.close()
        
    return {"charter": charter_data}
