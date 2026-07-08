from pydantic import BaseModel, Field
from typing import List


class DevOpsFile(BaseModel):
    path: str = Field(..., description="Relative path of the devops file (e.g. docker-compose.yml, k8s/deployment.yaml).")
    content: str = Field(..., description="Full content of the deployment file.")


class DevOpsManifests(BaseModel):
    """
    DevOpsManifests Pydantic contract returned by the DevOps Engineer Agent.
    """
    files: List[DevOpsFile] = Field(
        ...,
        description="List of all devops configuration and manifest files to write to disk."
    )
    container_tech: str = Field(
        default="Docker",
        description="Container technology used."
    )
    orchestration_tech: str = Field(
        default="Kubernetes",
        description="Orchestration platform used."
    )
