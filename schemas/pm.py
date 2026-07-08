from pydantic import BaseModel, Field
from typing import List

class UserStory(BaseModel):
    """
    User story representation.
    """
    role: str = Field(..., description="The user role (e.g., As an administrator...)")
    action: str = Field(..., description="The action the user wants to perform (e.g., I want to view logs...)")
    benefit: str = Field(..., description="The value or benefit of the action (e.g., So that I can debug errors...)")
    acceptance_criteria: List[str] = Field(..., description="List of acceptance criteria for this user story.")

class Feature(BaseModel):
    """
    System feature representation.
    """
    name: str = Field(..., description="The name of the feature.")
    description: str = Field(..., description="High-level description of what the feature does.")
    priority: str = Field(..., description="Priority level of the feature: 'High', 'Medium', or 'Low'.")
    complexity: str = Field(..., description="Complexity estimate: 'High', 'Medium', or 'Low'.")

class PRD(BaseModel):
    """
    Product Requirement Document (PRD) contract returned by the PM Agent.
    """
    user_stories: List[UserStory] = Field(
        ..., 
        description="List of target user stories for the application."
    )
    prioritized_features: List[Feature] = Field(
        ..., 
        description="Prioritized list of technical features to be implemented."
    )
    acceptance_criteria: List[str] = Field(
        ..., 
        description="Overall product-level acceptance criteria (e.g., Performance, Security)."
    )
