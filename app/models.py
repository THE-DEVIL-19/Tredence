# app/models.py

from typing import Any, Dict, List, Optional
from enum import Enum
from pydantic import BaseModel, Field


class NodeType(str, Enum):
    TOOL = "tool"


class NodeDefinition(BaseModel):
    id: str                 # Unique node id within a graph
    tool_name: str          # Name of the tool in the registry
    config: Dict[str, Any] = Field(default_factory=dict)


class EdgeDefinition(BaseModel):
    source: str             # Node id
    target: str             # Node id
    condition: Optional[str] = None
    # Example: "state['quality_score'] < state.get('threshold', 80)"


class GraphDefinition(BaseModel):
    id: str
    nodes: List[NodeDefinition]
    edges: List[EdgeDefinition]
    start_node_id: str


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class RunLogEntry(BaseModel):
    node_id: str
    state_snapshot: Dict[str, Any]
    message: Optional[str] = None


class RunState(BaseModel):
    run_id: str
    graph_id: str
    status: RunStatus
    current_node_id: Optional[str] = None
    state: Dict[str, Any] = Field(default_factory=dict)
    logs: List[RunLogEntry] = Field(default_factory=list)
