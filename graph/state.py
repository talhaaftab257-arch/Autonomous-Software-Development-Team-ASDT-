from typing import TypedDict, Dict, Any, List, Optional

class ProjectState(TypedDict):
    """
    ProjectState is the shared, stateful dictionary threaded through all nodes in the ASDT LangGraph.
    """
    run_id: str
    """Unique identifier for the current run."""

    business_requirement: str
    """The raw user input describing the application requirements."""

    charter: Optional[Dict[str, Any]]
    """Approved project charter: goals, constraints, metrics, status (from CEO Agent)."""

    prd: Optional[Dict[str, Any]]
    """Product Requirement Document: user stories, feature list, acceptance criteria (from PM Agent)."""

    requirements_doc: Optional[Dict[str, Any]]
    """Functional & non-functional requirements, data flows (from Business Analyst)."""

    architecture_spec: Optional[Dict[str, Any]]
    """System design: Mermaid system diagrams, DB schema, service boundaries (from Architect)."""

    ux_mockups: Optional[Dict[str, Any]]
    """Wireframes, UI mockups, component inventory (from UX Designer)."""

    frontend_code_path: Optional[str]
    """Path to the generated frontend React codebase (from Frontend Developer)."""

    backend_code_path: Optional[str]
    """Path to the generated FastAPI backend codebase (from Backend Developer)."""

    db_migrations_path: Optional[str]
    """Path to generated database schemas, migrations, and seed scripts (from DB Engineer)."""

    qa_results: Optional[Dict[str, Any]]
    """Test suite outputs, test runs, test coverage, and pending bugs list (from QA Engineer)."""

    security_report: Optional[Dict[str, Any]]
    """Static analysis reports (bandit, semgrep, eslint) and security findings (from Security Reviewer)."""

    deployment_manifests: Optional[Dict[str, Any]]
    """Dockerfiles, Compose files, and Kubernetes manifests (from DevOps Engineer)."""

    api_documentation: Optional[Dict[str, Any]]
    """README, Swagger/OpenAPI docs, ADRs (from Documentation Agent)."""

    errors: List[Dict[str, Any]]
    """History of errors raised during the run, mapped to the agents that encountered them."""

    qa_retry_count: int
    """Number of QA iteration retries currently performed (capped at 3)."""
    
    security_retry_count: int
    """Number of security remediation retries currently performed."""
