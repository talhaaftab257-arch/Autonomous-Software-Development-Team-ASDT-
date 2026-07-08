from pydantic import BaseModel, Field
from typing import List

class DatabaseFile(BaseModel):
    path: str = Field(..., description="Relative file path within the db project (e.g. migrations/001_init.sql).")
    content: str = Field(..., description="Full file content to write to disk.")

class DatabaseArtifacts(BaseModel):
    """
    DatabaseArtifacts Pydantic contract returned by the Database Engineer Agent.
    """
    files: List[DatabaseFile] = Field(
        ...,
        description="List of all database files to write: SQL migrations, seed data, alembic config."
    )
    migration_tool: str = Field(
        default="Alembic",
        description="Database migration tool used."
    )
    apply_command: str = Field(
        default="alembic upgrade head",
        description="Command to apply migrations."
    )
