# app/main.py

from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .models import (
    GraphDefinition,
    NodeDefinition,
    EdgeDefinition,
    RunState,
    RunLogEntry,
)
from .storage import graphs, runs
from .engine import run_graph_once
from .registry import tool_registry
from .workflows import register_default_tools, create_example_code_review_graph


app = FastAPI(
    title="Mini Agent Workflow Engine",
    description="A simple graph-based workflow engine with tools, branching, and loops.",
    version="0.1.0",
)


# --------- Startup: register tools and example graph --------- #

@app.on_event("startup")
async def on_startup() -> None:
    register_default_tools()
    create_example_code_review_graph()


# --------- Request / response models for the API --------- #

class GraphCreateRequest(BaseModel):
    nodes: List[NodeDefinition]
    edges: List[EdgeDefinition]
    start_node_id: str


class GraphCreateResponse(BaseModel):
    graph_id: str


class GraphRunRequest(BaseModel):
    graph_id: str
    initial_state: Dict[str, Any]


class GraphRunResponse(BaseModel):
    run_id: str
    final_state: Dict[str, Any]
    logs: List[RunLogEntry]
    status: str


class StateResponse(BaseModel):
    run_id: str
    status: str
    current_node_id: Optional[str]
    state: Dict[str, Any]
    logs: List[RunLogEntry]


# --------- Simple health check --------- #

@app.get("/")
async def root() -> Dict[str, str]:
    return {
        "message": "Mini Agent Workflow Engine is running",
        "example_graph_id": "code_review_graph",
    }


# --------- Endpoints --------- #

@app.post("/graph/create", response_model=GraphCreateResponse)
async def create_graph(req: GraphCreateRequest) -> GraphCreateResponse:
    """
    Create a new workflow graph at runtime.
    (Note: The assignment also provides a built-in 'code_review_graph' on startup.)
    """
    graph_id = str(uuid4())
    graph = GraphDefinition(
        id=graph_id,
        nodes=req.nodes,
        edges=req.edges,
        start_node_id=req.start_node_id,
    )
    graphs[graph_id] = graph
    return GraphCreateResponse(graph_id=graph_id)


@app.post("/graph/run", response_model=GraphRunResponse)
async def run_graph(req: GraphRunRequest) -> GraphRunResponse:
    """
    Execute a graph once from its start node with the given initial state.
    Returns the final state and execution logs.
    """
    if req.graph_id not in graphs:
        raise HTTPException(status_code=404, detail="Graph not found")

    run_state: RunState = await run_graph_once(
        graph_id=req.graph_id,
        initial_state=req.initial_state,
        registry=tool_registry,
    )

    return GraphRunResponse(
        run_id=run_state.run_id,
        final_state=run_state.state,
        logs=run_state.logs,
        status=run_state.status.value,
    )


@app.get("/graph/state/{run_id}", response_model=StateResponse)
async def get_graph_state(run_id: str) -> StateResponse:
    """
    Retrieve current state and logs for a specific run.
    This is most useful if you later implement long-running workflows.
    """
    if run_id not in runs:
        raise HTTPException(status_code=404, detail="Run not found")

    run_state = runs[run_id]
    return StateResponse(
        run_id=run_state.run_id,
        status=run_state.status.value,
        current_node_id=run_state.current_node_id,
        state=run_state.state,
        logs=run_state.logs,
    )
