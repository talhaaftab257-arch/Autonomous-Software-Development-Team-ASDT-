from pydantic import BaseModel, Field
from typing import List

class Wireframe(BaseModel):
    page_name: str = Field(..., description="Name of the page/view.")
    wireframe_description: str = Field(..., description="Description of layout and UI elements.")

class HTMLPrototype(BaseModel):
    page_name: str = Field(..., description="Name of the file (e.g. index.html).")
    html_content: str = Field(..., description="Complete drop-in static HTML content for prototype.")
    css_styles: str = Field(..., description="CSS styles embedded or linked for styling.")

class ComponentSpecification(BaseModel):
    component_name: str = Field(..., description="Name of the reusable UI component.")
    description: str = Field(..., description="Purpose and description of the component.")
    props: List[str] = Field(..., description="Props/Attributes needed for the component.")

class UXMockups(BaseModel):
    """
    UXMockups Pydantic contract returned by the UX/UI Designer Agent.
    """
    wireframes: List[Wireframe] = Field(
        ..., 
        description="Wireframe layout descriptions for each view."
    )
    html_prototypes: List[HTMLPrototype] = Field(
        ..., 
        description="Static HTML/CSS mockup templates representing the UI design."
    )
    component_inventory: List[ComponentSpecification] = Field(
        ..., 
        description="Inventory of modular UI components to build."
    )
