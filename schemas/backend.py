from pydantic import BaseModel, Field
from typing import List

class BackendFile(BaseModel):
    path: str = Field(..., description="Relative file path within the backend project (e.g. routers/tasks.py).")
    content: str = Field(..., description="Full file content to write to disk.")

class BackendCode(BaseModel):
    """
    BackendCode Pydantic contract returned by the Backend Developer Agent.
    """
    files: List[BackendFile] = Field(
        ...,
        description="List of all backend files to write, each with path and content."
    )
    framework: str = Field(
        default="FastAPI",
        description="Backend framework used."
    )
    install_command: str = Field(
        default="pip install -r requirements.txt",
        description="Command to install dependencies."
    )
    run_command: str = Field(
        default="uvicorn main:app --reload --port 8001",
        description="Command to run the backend dev server."
    )
