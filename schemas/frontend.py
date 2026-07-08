from pydantic import BaseModel, Field
from typing import List, Optional

class FrontendFile(BaseModel):
    path: str = Field(..., description="Relative file path within the frontend project (e.g. src/App.jsx).")
    content: str = Field(..., description="Full file content to write to disk.")

class FrontendCode(BaseModel):
    """
    FrontendCode Pydantic contract returned by the Frontend Developer Agent.
    """
    files: List[FrontendFile] = Field(
        ...,
        description="List of all frontend files to write, each with path and content."
    )
    framework: str = Field(
        default="React + Vite",
        description="Frontend framework used."
    )
    install_command: str = Field(
        default="npm install",
        description="Command to install dependencies."
    )
    dev_command: str = Field(
        default="npm run dev",
        description="Command to start the development server."
    )
