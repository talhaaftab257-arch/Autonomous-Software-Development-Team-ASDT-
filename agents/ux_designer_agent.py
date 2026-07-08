import os
import logging
from typing import Dict, Any
from datetime import datetime

from graph.state import ProjectState
from schemas.designer import UXMockups, Wireframe, HTMLPrototype, ComponentSpecification
from db.database import SessionLocal
from db.models import AgentOutput, RunEvent, ProjectRun

logger = logging.getLogger(__name__)

def generate_mock_mockups(architecture: Dict[str, Any], requirement: str) -> Dict[str, Any]:
    """
    Generates a high-quality mock UX/UI mockup specification and HTML contents.
    """
    req_lower = requirement.lower()
    
    if "task" in req_lower or "todo" in req_lower:
        wireframes = [
            {
                "page_name": "dashboard.html",
                "wireframe_description": "Dashboard containing active task lists, stats blocks (Pending, Active, Done), priority filter buttons, and a sidebar navigation."
            },
            {
                "page_name": "add_task.html",
                "wireframe_description": "A modal or single page form with fields: Title, Description, Priority (Select), Tags (Input), and Save/Cancel buttons."
            }
        ]
        
        # HTML template for a gorgeous task dashboard
        dashboard_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TaskFlow Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #0f172a;
            --card-bg: rgba(30, 41, 59, 0.7);
            --border-color: rgba(255, 255, 255, 0.08);
            --primary: #3b82f6;
            --primary-glow: rgba(59, 130, 246, 0.15);
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
        }

        body {
            background-color: var(--bg-color);
            color: var(--text-main);
            font-family: 'Outfit', sans-serif;
            margin: 0;
            padding: 0;
            display: flex;
            min-height: 100vh;
        }

        /* Sidebar styling */
        .sidebar {
            width: 260px;
            background: rgba(15, 23, 42, 0.95);
            border-right: 1px solid var(--border-color);
            padding: 2rem 1.5rem;
            display: flex;
            flex-direction: column;
            gap: 2rem;
        }

        .logo {
            font-size: 1.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, #3b82f6, #8b5cf6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .menu-list {
            list-style: none;
            padding: 0;
            margin: 0;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }

        .menu-item {
            padding: 0.75rem 1rem;
            border-radius: 0.5rem;
            color: var(--text-muted);
            text-decoration: none;
            font-weight: 500;
            transition: all 0.3s;
            cursor: pointer;
        }

        .menu-item:hover, .menu-item.active {
            color: var(--text-main);
            background: rgba(255, 255, 255, 0.05);
            box-shadow: inset 0 0 10px rgba(255,255,255,0.02);
        }

        /* Main Content Grid */
        .main-content {
            flex: 1;
            padding: 2.5rem;
            overflow-y: auto;
            max-width: 1200px;
            margin: 0 auto;
            width: 100%;
        }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2.5rem;
        }

        h1 {
            margin: 0;
            font-size: 2.25rem;
            font-weight: 700;
        }

        .btn-primary {
            background: linear-gradient(135deg, #3b82f6, #2563eb);
            border: none;
            color: white;
            padding: 0.75rem 1.5rem;
            border-radius: 0.5rem;
            font-weight: 600;
            cursor: pointer;
            box-shadow: 0 4px 15px var(--primary-glow);
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(59, 130, 246, 0.3);
        }

        /* Stats Section */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2.5rem;
        }

        .stat-card {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 1rem;
            padding: 1.5rem;
            backdrop-filter: blur(12px);
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }

        .stat-label {
            color: var(--text-muted);
            font-size: 0.875rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .stat-value {
            font-size: 2rem;
            font-weight: 700;
        }

        /* Tasks Layout */
        .task-list {
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }

        .task-card {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 0.75rem;
            padding: 1.25rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: border-color 0.3s;
            cursor: pointer;
        }

        .task-card:hover {
            border-color: rgba(59, 130, 246, 0.4);
        }

        .task-info {
            display: flex;
            flex-direction: column;
            gap: 0.35rem;
        }

        .task-title {
            font-size: 1.125rem;
            font-weight: 600;
        }

        .task-desc {
            color: var(--text-muted);
            font-size: 0.875rem;
        }

        .tags-container {
            display: flex;
            gap: 0.5rem;
            margin-top: 0.25rem;
        }

        .tag {
            background: rgba(255, 255, 255, 0.05);
            padding: 0.2rem 0.6rem;
            border-radius: 0.25rem;
            font-size: 0.75rem;
            color: var(--text-muted);
        }

        .badge {
            padding: 0.35rem 0.75rem;
            border-radius: 2rem;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }

        .badge.high { background: rgba(239, 68, 68, 0.15); color: var(--danger); }
        .badge.medium { background: rgba(245, 158, 11, 0.15); color: var(--warning); }
        .badge.low { background: rgba(16, 185, 129, 0.15); color: var(--success); }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="logo">⚡ TaskFlow</div>
        <ul class="menu-list">
            <li><a class="menu-item active">Dashboard</a></li>
            <li><a class="menu-item">My Tasks</a></li>
            <li><a class="menu-item">Categories</a></li>
            <li><a class="menu-item">Settings</a></li>
        </ul>
    </div>
    
    <div class="main-content">
        <header>
            <div>
                <h1>Task Management</h1>
                <p style="color: var(--text-muted); margin: 0.25rem 0 0 0;">Welcome back! Here's your task inventory.</p>
            </div>
            <button class="btn-primary" onclick="alert('Open Task Modal')">+ New Task</button>
        </header>

        <div class="stats-grid">
            <div class="stat-card">
                <span class="stat-label">Pending</span>
                <span class="stat-value" style="color: var(--warning);">3</span>
            </div>
            <div class="stat-card">
                <span class="stat-label">Active</span>
                <span class="stat-value" style="color: var(--primary);">2</span>
            </div>
            <div class="stat-card">
                <span class="stat-label">Completed</span>
                <span class="stat-value" style="color: var(--success);">5</span>
            </div>
        </div>

        <h2 style="font-size: 1.5rem; margin-bottom: 1rem;">Active Tasks</h2>
        <div class="task-list">
            <div class="task-card">
                <div class="task-info">
                    <span class="task-title">Implement Secure OAuth Authentication</span>
                    <span class="task-desc">Set up session token creation and database password salting.</span>
                    <div class="tags-container">
                        <span class="tag">Security</span>
                        <span class="tag">Backend</span>
                    </div>
                </div>
                <span class="badge high">High Priority</span>
            </div>
            
            <div class="task-card">
                <div class="task-info">
                    <span class="task-title">Design Modern Dark-Mode Layout</span>
                    <span class="task-desc">Create glassmorphism dashboard structures using CSS HSL colors.</span>
                    <div class="tags-container">
                        <span class="tag">UX/UI</span>
                        <span class="tag">Frontend</span>
                    </div>
                </div>
                <span class="badge medium">Medium Priority</span>
            </div>
            
            <div class="task-card">
                <div class="task-info">
                    <span class="task-title">Seed Initial SQLite Database</span>
                    <span class="task-desc">Create seed scripts for users, tasks, and initial categorization tags.</span>
                    <div class="tags-container">
                        <span class="tag">DB</span>
                    </div>
                </div>
                <span class="badge low">Low Priority</span>
            </div>
        </div>
    </div>
</body>
</html>
"""
        
        html_prototypes = [
            {
                "page_name": "dashboard.html",
                "html_content": dashboard_html,
                "css_styles": "Included inline"
            }
        ]
        
        components = [
            {
                "component_name": "Sidebar",
                "description": "Navigation sidebar for quick tab switching.",
                "props": ["items", "activeItem", "onNavigate"]
            },
            {
                "component_name": "TaskCard",
                "description": "Individual task item with title, priority badge, and tag markers.",
                "props": ["title", "description", "priority", "tags", "onCheck"]
            },
            {
                "component_name": "StatCard",
                "description": "Metric indicator displaying numerical values with status colors.",
                "props": ["label", "value", "colorTheme"]
            }
        ]
    else:
        # Standard placeholder mockups
        wireframes = [{"page_name": "index.html", "wireframe_description": "Standard base index layout."}]
        html_prototypes = [
            {
                "page_name": "index.html",
                "html_content": f"<html><body><h1>Resource Dashboard</h1><p>Running for: {requirement}</p></body></html>",
                "css_styles": "body { font-family: sans-serif; }"
            }
        ]
        components = [{"component_name": "Header", "description": "Global Header", "props": []}]

    return {
        "wireframes": wireframes,
        "html_prototypes": html_prototypes,
        "component_inventory": components
    }

def designer_node(state: ProjectState) -> Dict[str, Any]:
    """
    UX/UI Designer Agent Node.
    Generates wireframe specifications, HTML templates, and component list.
    """
    run_id = state.get("run_id")
    architecture = state.get("architecture_spec")
    requirement = state.get("business_requirement", "")
    
    if not architecture:
        raise ValueError("architecture_spec is missing in state. Solution Architect node must run first.")

    # Initialize Database Session
    db = SessionLocal()
    
    # Log starting event
    start_event = RunEvent(
        run_id=run_id,
        agent_name="UX Designer",
        status="STARTED",
        message="UX Agent starting UI prototype drafts."
    )
    db.add(start_event)
    db.commit()

    mockups_data = None
    api_key = os.getenv("ANTHROPIC_API_KEY")
    is_mock = not api_key or api_key == "your-anthropic-api-key-here" or api_key.startswith("your-")
    
    if not is_mock:
        try:
            from langchain_anthropic import ChatAnthropic
            
            llm = ChatAnthropic(model="claude-3-5-sonnet-20240620", temperature=0)
            structured_llm = llm.with_structured_output(UXMockups)
            
            prompt = (
                f"You are the UX/UI Designer Agent.\n"
                f"Generate wireframes, reusable component specs, and complete static HTML/CSS template codes based on this architecture.\n\n"
                f"Architecture Details:\n{architecture}"
            )
            
            result = structured_llm.invoke(prompt)
            mockups_data = result.dict()
            logger.info("UX Designer Agent generated mockups using Anthropic LLM.")
        except Exception as e:
            logger.error(f"UX Designer Agent LLM call failed. Falling back to mock. Error: {e}")

    if mockups_data is None:
        mockups_data = generate_mock_mockups(architecture, requirement)
        logger.info("UX Designer Agent generated mockups using local mock fallback.")

    try:
        # Save output to agent_outputs table
        output_record = AgentOutput(
            run_id=run_id,
            agent_name="UX Designer",
            artifact_type="ux_mockups",
            content=mockups_data
        )
        db.add(output_record)
        
        # PHYSICAL MOCKUP FILE WRITING
        # Write pages on disk to generated_projects/{run_id}/mockups/
        mockup_dir = os.path.join("generated_projects", run_id, "mockups")
        os.makedirs(mockup_dir, exist_ok=True)
        
        written_paths = []
        for proto in mockups_data.get("html_prototypes", []):
            page_name = proto.get("page_name", "index.html")
            content = proto.get("html_content", "")
            
            file_path = os.path.join(mockup_dir, page_name)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            written_paths.append(file_path)
            
        # Log completion event
        complete_event = RunEvent(
            run_id=run_id,
            agent_name="UX Designer",
            status="COMPLETED",
            message=f"UX Agent completed UI design templates. Wrote {len(written_paths)} mockup file(s) to generated_projects/{run_id}/mockups/."
        )
        db.add(complete_event)
        
        # Update current agent in project_runs
        run_record = db.query(ProjectRun).filter(ProjectRun.id == run_id).first()
        if run_record:
            run_record.current_agent = "UX Designer"
            
        db.commit()
    except Exception as db_err:
        db.rollback()
        logger.error(f"UX Designer Agent database logging or file writing failed: {db_err}")
        raise db_err
    finally:
        db.close()
        
    return {"ux_mockups": mockups_data}
