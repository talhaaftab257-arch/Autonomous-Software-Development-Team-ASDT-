from pydantic import BaseModel, Field
from typing import List

class RequirementsDoc(BaseModel):
    """
    RequirementsDoc Pydantic contract returned by the Business Analyst Agent.
    """
    functional_requirements: List[str] = Field(
        ..., 
        description="Detailed functional requirements outlining system behavior and features."
    )
    non_functional_requirements: List[str] = Field(
        ..., 
        description="Non-functional requirements such as performance, security, and scalability."
    )
    data_flow_notes: List[str] = Field(
        ..., 
        description="Notes on data flows, input/output structures, and interface definitions."
    )
