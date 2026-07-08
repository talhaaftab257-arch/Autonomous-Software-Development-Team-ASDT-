from pydantic import BaseModel, Field
from typing import List


class DocFile(BaseModel):
    path: str = Field(..., description="Relative path of the document (e.g. README.md, docs/openapi.json).")
    content: str = Field(..., description="Full content of the document.")


class ApiDocs(BaseModel):
    """
    ApiDocs Pydantic contract returned by the Documentation Agent.
    """
    files: List[DocFile] = Field(
        ...,
        description="List of all documentation files, including READMEs, OpenAPI specs, and ADRs."
    )
    format: str = Field(
        default="Markdown + JSON",
        description="Documentation format used."
    )
