from pydantic import BaseModel, Field
from typing import List

class ProjectCharter(BaseModel):
    """
    ProjectCharter Pydantic contract returned by the CEO Agent.
    """
    goals: List[str] = Field(
        ..., 
        description="High-level goals of the project defining what we want to achieve."
    )
    constraints: List[str] = Field(
        ..., 
        description="Technical and business constraints (e.g., tech stack, timelines)."
    )
    success_metrics: List[str] = Field(
        ..., 
        description="Key metrics to measure the success of the project."
    )
    go_or_no_go: bool = Field(
        ..., 
        description="A clear decision whether to proceed (True) or stop (False) the project."
    )
    reasoning: str = Field(
        ..., 
        description="Detailed explanation/reasoning behind the go/no-go decision."
    )
