import os
import json
import logging
from typing import Dict, Any

from graph.state import ProjectState
from schemas.qa import QAResults, TestSuite, Bug
from db.database import SessionLocal
from db.models import AgentOutput, RunEvent, ProjectRun

logger = logging.getLogger(__name__)


def generate_mock_qa_results(frontend_path: str, backend_path: str, retry_count: int) -> Dict[str, Any]:
    """
    Generates simulated QA test results and an HTML report.
    To demonstrate LangGraph's self-healing loop-back, we'll return a simulated bug on the first run,
    and then pass cleanly on subsequent runs (or if retry_count > 0).
    """
    # If it's the first run (retry_count == 0), simulate a minor bug to trigger loop-back.
    # Otherwise, simulate all tests passing.
    has_bug = (retry_count == 0)

    bugs = []
    if has_bug:
        bugs.append({
            "id": "BUG-001",
            "title": "CORS preflight request failing on Task creation",
            "severity": "High",
            "location": "backend/main.py:L20-L30",
            "description": "The React frontend at port 3000 is unable to make POST requests to port 8001 due to missing CORS headers for Task creation preflight checks.",
            "recommendation": "Ensure CORS middleware is correctly configured in FastAPI main.py to allow http://localhost:3000."
        })

    backend_passed = 8 if not has_bug else 7
    backend_failed = 0 if not has_bug else 1

    test_suites = [
        {
            "name": "Backend Unit Tests",
            "total_tests": 8,
            "passed": backend_passed,
            "failed": backend_failed,
            "skipped": 0,
            "coverage_percent": 88.5,
            "output_snippet": "test_health PASSED\ntest_create_task PASSED\ntest_list_tasks PASSED\ntest_complete_task " + 
                              ("PASSED" if not has_bug else "FAILED (CORS Error)")
        },
        {
            "name": "Frontend Component Tests",
            "total_tests": 5,
            "passed": 5,
            "failed": 0,
            "skipped": 0,
            "coverage_percent": 75.0,
            "output_snippet": "App renders correctly PASSED\nTaskCard renders correctly PASSED\nStatCard displays values PASSED"
        },
        {
            "name": "End-to-End Integration Tests",
            "total_tests": 3,
            "passed": 3 if not has_bug else 2,
            "failed": 0 if not has_bug else 1,
            "skipped": 0,
            "coverage_percent": 90.0,
            "output_snippet": "Full task lifecycle integration: " + ("PASSED" if not has_bug else "FAILED")
        }
    ]

    total_tests = sum(s["total_tests"] for s in test_suites)
    total_passed = sum(s["passed"] for s in test_suites)
    total_failed = sum(s["failed"] for s in test_suites)
    overall_coverage = sum(s["coverage_percent"] for s in test_suites) / len(test_suites)
    overall_status = "FAILED" if total_failed > 0 else "PASSED"

    return {
        "overall_status": overall_status,
        "test_suites": test_suites,
        "total_tests": total_tests,
        "total_passed": total_passed,
        "total_failed": total_failed,
        "overall_coverage": round(overall_coverage, 2),
        "bugs": bugs
    }


def qa_node(state: ProjectState) -> Dict[str, Any]:
    """
    QA Engineer Agent Node.

    Input:
        - frontend_code_path (str)
        - backend_code_path (str)
        - qa_retry_count (int)

    Output:
        - qa_results (dict)
        - qa_retry_count (int)
    """
    run_id = state.get("run_id")
    frontend_path = state.get("frontend_code_path")
    backend_path = state.get("backend_code_path")
    retry_count = state.get("qa_retry_count", 0)

    if not frontend_path or not backend_path:
        raise ValueError("frontend_code_path and backend_code_path are required. Developers must run first.")

    db = SessionLocal()
    db.add(RunEvent(run_id=run_id, agent_name="QA Engineer", status="STARTED",
                    message=f"QA Engineer starting test execution. Run iteration: {retry_count + 1}"))
    db.commit()

    qa_data = None
    api_key = os.getenv("ANTHROPIC_API_KEY")
    is_mock = not api_key or api_key.startswith("your-")

    if not is_mock:
        try:
            from langchain_anthropic import ChatAnthropic
            llm = ChatAnthropic(model="claude-3-5-sonnet-20240620", temperature=0)
            structured_llm = llm.with_structured_output(QAResults)
            result = structured_llm.invoke(
                f"You are the QA Engineer Agent. Run simulated unit and integration tests for this project.\n"
                f"Frontend Path: {frontend_path}\n"
                f"Backend Path: {backend_path}\n"
                f"Retry Count: {retry_count}\n"
                f"Return test suites, coverages, and any bugs found."
            )
            qa_data = result.dict()
        except Exception as e:
            logger.error(f"QA Agent LLM failed, using mock: {e}")

    if qa_data is None:
        qa_data = generate_mock_qa_results(frontend_path, backend_path, retry_count)

    # Write QA HTML Report to disk
    report_dir = os.path.join("generated_projects", run_id, "qa")
    os.makedirs(report_dir, exist_ok=True)
    report_file_path = os.path.join(report_dir, "report.html")

    bugs_list_html = ""
    for bug in qa_data["bugs"]:
        bugs_list_html += f"""
        <div class="bug-card">
            <h3>[{bug['id']}] {bug['title']} - <span class="severity">{bug['severity']}</span></h3>
            <p><strong>Location:</strong> {bug['location']}</p>
            <p><strong>Description:</strong> {bug['description']}</p>
            <p><strong>Recommendation:</strong> {bug['recommendation']}</p>
        </div>
        """

    if not bugs_list_html:
        bugs_list_html = "<p class='no-bugs'>No open bugs! All tests passed successfully.</p>"

    suites_html = ""
    for suite in qa_data["test_suites"]:
        suites_html += f"""
        <div class="suite-card">
            <h3>{suite['name']}</h3>
            <p>Passed: {suite['passed']} / {suite['total_tests']} | Coverage: {suite['coverage_percent']}%</p>
            <pre>{suite['output_snippet']}</pre>
        </div>
        """

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>QA Test Report</title>
    <style>
        body {{ font-family: sans-serif; background: #0f172a; color: #f8fafc; padding: 20px; }}
        h1, h2 {{ color: #3b82f6; }}
        .summary {{ background: #1e293b; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
        .suite-card, .bug-card {{ background: #1e293b; padding: 15px; border-radius: 8px; margin-bottom: 10px; border: 1px solid #334155; }}
        .bug-card {{ border-left: 5px solid #ef4444; }}
        .severity {{ color: #ef4444; font-weight: bold; }}
        .no-bugs {{ color: #10b981; font-weight: bold; }}
        pre {{ background: #0f172a; padding: 10px; border-radius: 4px; color: #38bdf8; }}
    </style>
</head>
<body>
    <h1>ASDT QA Test Report</h1>
    <div class="summary">
        <h2>Overall Verdict: {qa_data['overall_status']}</h2>
        <p>Total Tests: {qa_data['total_tests']} | Passed: {qa_data['total_passed']} | Failed: {qa_data['total_failed']}</p>
        <p>Overall Coverage: {qa_data['overall_coverage']}%</p>
    </div>
    
    <h2>Test Suites</h2>
    {suites_html}
    
    <h2>Detected Bugs</h2>
    {bugs_list_html}
</body>
</html>
"""
    with open(report_file_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    qa_data["report_path"] = report_file_path

    new_retry_count = retry_count
    if qa_data["bugs"]:
        new_retry_count += 1

    try:
        db.add(AgentOutput(run_id=run_id, agent_name="QA Engineer",
                           artifact_type="qa_results",
                           content=qa_data))
        db.add(RunEvent(run_id=run_id, agent_name="QA Engineer", status="COMPLETED",
                        message=f"QA test suite run complete. Status: {qa_data['overall_status']}. Bugs found: {len(qa_data['bugs'])}"))
        run_rec = db.query(ProjectRun).filter(ProjectRun.id == run_id).first()
        if run_rec:
            run_rec.current_agent = "QA Engineer"
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

    return {"qa_results": qa_data, "qa_retry_count": new_retry_count}
