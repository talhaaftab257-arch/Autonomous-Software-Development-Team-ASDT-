from pydantic import BaseModel, Field
from typing import List, Optional


class SecurityFinding(BaseModel):
    id: str = Field(..., description="Finding identifier, e.g. SEC-001.")
    title: str = Field(..., description="Short title of the vulnerability.")
    severity: str = Field(..., description="Critical / High / Medium / Low / Info.")
    category: str = Field(..., description="OWASP category, e.g. A03:Injection, A07:Auth Failures.")
    location: str = Field(..., description="File path and line where the vulnerability exists.")
    description: str = Field(..., description="Detailed description of the vulnerability.")
    recommendation: str = Field(..., description="Specific remediation steps.")
    cwe_id: Optional[str] = Field(default=None, description="Common Weakness Enumeration ID, e.g. CWE-89.")


class SecurityReport(BaseModel):
    """
    SecurityReport Pydantic contract returned by the Security Reviewer Agent.
    """
    overall_risk: str = Field(
        ..., description="LOW / MEDIUM / HIGH / CRITICAL — overall risk rating."
    )
    findings: List[SecurityFinding] = Field(
        default_factory=list,
        description="All security findings. Empty means no issues detected."
    )
    total_findings: int = Field(..., description="Total count of all findings.")
    critical_count: int = Field(default=0, description="Number of Critical severity findings.")
    high_count: int = Field(default=0, description="Number of High severity findings.")
    medium_count: int = Field(default=0, description="Number of Medium severity findings.")
    low_count: int = Field(default=0, description="Number of Low/Info findings.")
    tools_used: List[str] = Field(
        default_factory=list,
        description="Static analysis tools that were simulated, e.g. ['bandit', 'semgrep', 'eslint']."
    )
    passed_checks: List[str] = Field(
        default_factory=list,
        description="Security checks that passed without issues."
    )
    report_path: Optional[str] = Field(
        default=None, description="Path to the full security report on disk."
    )
