import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base, engine

class ProjectRun(Base):
    __tablename__ = "project_runs"

    id = Column(String(100), primary_key=True, index=True) # run_id / project_id
    business_requirement = Column(Text, nullable=False)
    status = Column(String(50), default="INITIATED")
    current_agent = Column(String(50), nullable=True)
    state_snapshot = Column(JSON, nullable=True) # Serialized LangGraph state
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    outputs = relationship("AgentOutput", back_populates="run", cascade="all, delete-orphan")
    events = relationship("RunEvent", back_populates="run", cascade="all, delete-orphan")

class AgentOutput(Base):
    __tablename__ = "agent_outputs"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String(100), ForeignKey("project_runs.id"), nullable=False)
    agent_name = Column(String(50), nullable=False)
    artifact_type = Column(String(100), nullable=False) # e.g., charter, prd, architecture
    content = Column(JSON, nullable=False) # JSON payload matching the Pydantic edge contract
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    run = relationship("ProjectRun", back_populates="outputs")

class RunEvent(Base):
    __tablename__ = "run_events"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String(100), ForeignKey("project_runs.id"), nullable=False)
    agent_name = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False) # e.g., STARTED, COMPLETED, FAILED
    message = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    run = relationship("ProjectRun", back_populates="events")

# Create tables
def init_db():
    Base.metadata.create_all(bind=engine)
