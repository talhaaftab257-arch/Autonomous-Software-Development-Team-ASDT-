from pydantic import BaseModel, Field
from typing import List, Optional


class Bug(BaseModel):
    id: str = Field(..., description="Short bug identifier, e.g. BUG-001.")
    title: str = Field(..., description="One-line summary of the bug.")
    severity: str = Field(..., description="Critical / High / Medium / Low.")
    location: str = Field(..., description="File path and line range where the bug was found.")
    description: str = Field(..., description="Detailed description of the bug and its impact.")
    recommendation: str = Field(..., description="Recommended fix or workaround.")


class TestSuite(BaseModel):
    name: str = Field(..., description="Name of the test suite, e.g. 'Backend Unit Tests'.")
    total_tests: int = Field(..., description="Total number of tests in the suite.")
    passed: int = Field(..., description="Number of passing tests.")
    failed: int = Field(..., description="Number of failing tests.")
    skipped: int = Field(default=0, description="Number of skipped tests.")
    coverage_percent: float = Field(..., description="Code coverage percentage for this suite.")
    output_snippet: str = Field(default="", description="Abbreviated test runner output.")


class QAResults(BaseModel):
    """
    QAResults Pydantic contract returned by the QA Engineer Agent.
    """
    overall_status: str = Field(
        ..., description="PASSED / FAILED / PARTIAL — overall QA verdict."
    )
    test_suites: List[TestSuite] = Field(
        ..., description="Results for each test suite run (backend, frontend, integration)."
    )
    total_tests: int = Field(..., description="Total tests across all suites.")
    total_passed: int = Field(..., description="Total passing tests across all suites.")
    total_failed: int = Field(..., description="Total failing tests across all suites.")
    overall_coverage: float = Field(..., description="Weighted average code coverage percent.")
    bugs: List[Bug] = Field(
        default_factory=list,
        description="List of bugs detected. Empty list means all tests passed cleanly."
    )
    report_path: Optional[str] = Field(
        default=None, description="Path to the full HTML test report on disk."
    )
