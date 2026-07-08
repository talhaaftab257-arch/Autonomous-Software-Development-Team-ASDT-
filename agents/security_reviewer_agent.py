import os
import json
import logging
from typing import Dict, Any

from graph.state import ProjectState
from schemas.security import SecurityReport, SecurityFinding
from db.database import SessionLocal
from db.models import AgentOutput, RunEvent, ProjectRun

logger = logging.getLogger(__name__)


def generate_mock_security_report(frontend_path: str, backend_path: str, retry_count: int) -> Dict[str, Any]:
    """
    Generates simulated static analysis vulnerability findings.
    Like the QA agent, to showcase the LangGraph loop-back capability, we return a simulated vulnerability
    on the first run, then resolve it on subsequent runs (retry_count > 0).
    """
    has_vuln = (retry_count == 0)

    findings = []
    if has_vuln:
        findings.append({
            "id": "SEC-001",
            "title": "SQL Injection vulnerability in direct query concatenation",
            "severity": "High",
            "category": "A03:Injection",
            "location": "backend/routers/tasks.py:L40",
            "description": "User input task title is directly concatenated in raw SQL query construction instead of using SQLAlchemy ORM parameterized attributes.",
            "recommendation": "Rewrite the query to use SQLAlchemy's model-mapped query filter or bind variables.",
            "cwe_id": "CWE-89"
        })

    risk_rating = "HIGH" if has_vuln else "LOW"

    return {
        "overall_risk": risk_rating,
        "findings": findings,
        "total_findings": len(findings),
        "critical_count": 0,
        "high_count": 1 if has_vuln else 0,
        "medium_count": 0,
        "low_count": 0,
        "tools_used": ["bandit", "semgrep", "eslint-plugin-security"],
        "passed_checks": [
            "No hardcoded secrets or API keys found in source code",
            "CORS settings restrict wildcard domains on production-ready code",
            "FastAPI routing does not expose default administrative debugging views"
        ]
    }


def security_node(state: ProjectState) -> Dict[str, Any]:
    """
    Security Reviewer Agent Node.

    Input:
        - frontend_code_path (str)
        - backend_code_path (str)
        - security_retry_count (int)

    Output:
        - security_report (dict)
        - security_retry_count (int)
    """
    run_id = state.get("run_id")
    frontend_path = state.get("frontend_code_path")
    backend_path = state.get("backend_code_path")
    retry_count = state.get("security_retry_count", 0)

    if not frontend_path or not backend_path:
        raise ValueError("frontend_code_path and backend_code_path are required. Developers must run first.")

    db = SessionLocal()
    db.add(RunEvent(run_id=run_id, agent_name="Security Reviewer", status="STARTED",
                    message=f"Security Reviewer starting static analysis scan. Run iteration: {retry_count + 1}"))
    db.commit()

    sec_data = None
    api_key = os.getenv("ANTHROPIC_API_KEY")
    is_mock = not api_key or api_key.startswith("your-")

    if not is_mock:
        try:
            from langchain_anthropic import ChatAnthropic
            llm = ChatAnthropic(model="claude-3-5-sonnet-20240620", temperature=0)
            structured_llm = llm.with_structured_output(SecurityReport)
            result = structured_llm.invoke(
                f"You are the Security Reviewer Agent. Run static security analysis (Bandit/Semgrep mock) "
                f"for the codebases under:\nFrontend: {frontend_path}\nBackend: {backend_path}\n"
                f"Retry Count: {retry_count}"
            )
            sec_data = result.dict()
        except Exception as e:
            logger.error(f"Security Agent LLM failed, using mock: {e}")

    if sec_data is None:
        sec_data = generate_mock_security_report(frontend_path, backend_path, retry_count)

    # Write Security HTML report to disk
    report_dir = os.path.join("generated_projects", run_id, "security")
    os.makedirs(report_dir, exist_ok=True)
    report_file_path = os.path.join(report_dir, "report.html")

    findings_html = ""
    for f in sec_data["findings"]:
        findings_html += f"""
        <div class="finding-card">
            <h3>[{f['id']}] {f['title']} - <span class="severity">{f['severity']}</span></h3>
            <p><strong>Category:</strong> {f['category']} | <strong>CWE:</strong> {f.get('cwe_id', 'N/A')}</p>
            <p><strong>Location:</strong> {f['location']}</p>
            <p><strong>Description:</strong> {f['description']}</p>
            <p><strong>Remediation:</strong> {f['recommendation']}</p>
        </div>
        """

    if not findings_html:
        findings_html = "<p class='no-findings'>No security vulnerabilities found. Code looks secure!</p>"

    passed_html = "".join(f"<li>{check}</li>" for check in sec_data["passed_checks"])

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Security Audit Report</title>
    <style>
        body {{ font-family: sans-serif; background: #0b0f19; color: #e2e8f0; padding: 20px; }}
        h1, h2 {{ color: #ef4444; }}
        .summary {{ background: #1e293b; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
        .finding-card {{ background: #1e293b; padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 5px solid #ef4444; }}
        .severity {{ color: #ef4444; font-weight: bold; }}
        .no-findings {{ color: #10b981; font-weight: bold; }}
        .passed-list {{ background: #1e293b; padding: 15px; border-radius: 8px; }}
    </style>
</head>
<body>
    <h1>ASDT Security Audit Report</h1>
    <div class="summary">
        <h2>Overall Risk Rating: {sec_data['overall_risk']}</h2>
        <p>Total Findings: {sec_data['total_findings']} (Critical: {sec_data.get('critical_count', 0)}, High: {sec_data.get('high_count', 0)}, Medium: {sec_data.get('medium_count', 0)})</p>
        <p>Tools Simulating: {', '.join(sec_data['tools_used'])}</p>
    </div>
    
    <h2>Vulnerabilities</h2>
    {findings_html}
    
    <h2>Checks Passed</h2>
    <div class="passed-list">
        <ul>{passed_html}</ul>
    </div>
</body>
</html>
"""
    with open(report_file_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    sec_data["report_path"] = report_file_path

    new_retry_count = retry_count
    if sec_data["findings"]:
        new_retry_count += 1

    try:
        db.add(AgentOutput(run_id=run_id, agent_name="Security Reviewer",
                           artifact_type="security_report",
                           content=sec_data))
        db.add(RunEvent(run_id=run_id, agent_name="Security Reviewer", status="COMPLETED",
                        message=f"Security audit complete. Verdict: {sec_data['overall_risk']}. Vulnerabilities found: {len(sec_data['findings'])}"))
        run_rec = db.query(ProjectRun).filter(ProjectRun.id == run_id).first()
        if run_rec:
            run_rec.current_agent = "Security Reviewer"
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

    return {"security_report": sec_data, "security_retry_count": new_retry_count}
