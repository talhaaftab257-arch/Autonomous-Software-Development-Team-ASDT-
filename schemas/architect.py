from pydantic import BaseModel, Field
from typing import List, Dict

class ServiceBoundary(BaseModel):
    name: str = Field(..., description="Name of the service or component boundary.")
    description: str = Field(..., description="What the service is responsible for.")
    technology: str = Field(..., description="Technology stack chosen for this service.")

class DatabaseTable(BaseModel):
    table_name: str = Field(..., description="Name of the database table.")
    columns: List[str] = Field(..., description="List of columns and their types.")
    relationships: List[str] = Field(..., description="List of foreign keys and relationships.")

class ArchitectureSpec(BaseModel):
    """
    ArchitectureSpec Pydantic contract returned by the Solution Architect Agent.
    """
    mermaid_diagram: str = Field(
        ..., 
        description="Mermaid diagram representing the system architecture (e.g. graph TD)."
    )
    service_boundaries: List[ServiceBoundary] = Field(
        ..., 
        description="Logical service boundaries dividing the application."
    )
    database_schema: List[DatabaseTable] = Field(
        ..., 
        description="Declarative database schema tables and relationships."
    )
    tech_choices: Dict[str, str] = Field(
        ..., 
        description="Key/value pairs of component names and chosen technologies (e.g., 'frontend': 'React')."
    )
