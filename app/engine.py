# app/engine.py

from typing import Dict, Optional
from uuid import uuid4

from .models import (
    GraphDefinition,
    RunState,
    RunStatus,
    RunLogEntry,
    EdgeDefinition,
)
from .storage import graphs, runs
from .registry import ToolRegistry


def _find_next_edge(
    graph: GraphDefinition,
    current_node_id: str,
    state: Dict
) -> Optional[EdgeDefinition]:
    """
    Find the next edge from the current node whose condition passes.
    If no edges or no conditions pass, return None.
    """
    candidates = [e for e in graph.edges if e.source == current_node_id]
    if not candidates:
        return None

    for edge in candidates:
        # If no condition, treat as default edge
        if edge.condition is None:
            return edge

        # Very naive: evaluate the condition as Python.
        # For production, replace with a proper DSL or safe evaluator.
        local_ctx = {"state": state}
        try:
            if bool(eval(edge.condition, {}, local_ctx)):
                return edge
        except Exception:
            # If condition evaluation fails, skip this edge
            continue

    return None


async def run_graph_once(
    graph_id: str,
    initial_state: Dict,
    registry: ToolRegistry,
    max_steps: int = 100
) -> RunState:
    """
    Execute a graph from its start node until no next edge is found
    or max_steps is exceeded. Supports branching and loops.
    """
    if graph_id not in graphs:
        raise KeyError(f"Graph '{graph_id}' not found")

    graph: GraphDefinition = graphs[graph_id]
    run_id = str(uuid4())

    run_state = RunState(
        run_id=run_id,
        graph_id=graph_id,
        status=RunStatus.RUNNING,
        current_node_id=graph.start_node_id,
        state=initial_state.copy(),
        logs=[],
    )
    runs[run_id] = run_state

    current_node_id = graph.start_node_id

    for _ in range(max_steps):
        # Find node
        try:
            node = next(n for n in graph.nodes if n.id == current_node_id)
        except StopIteration:
            run_state.status = RunStatus.FAILED
            run_state.logs.append(
                RunLogEntry(
                    node_id=current_node_id,
                    state_snapshot=run_state.state.copy(),
                    message=f"Node '{current_node_id}' not found in graph",
                )
            )
            break

        # Run the tool for this node
        tool_result = await registry.run_tool(node.tool_name, run_state.state)
        run_state.state.update(tool_result)

        run_state.logs.append(
            RunLogEntry(
                node_id=node.id,
                state_snapshot=run_state.state.copy(),
                message=f"Executed tool '{node.tool_name}'",
            )
        )

        # Find the next edge
        next_edge = _find_next_edge(graph, current_node_id, run_state.state)
        if not next_edge:
            # No next edge: workflow complete
            run_state.status = RunStatus.COMPLETED
            run_state.current_node_id = None
            break

        # Move to the next node (supports loops)
        current_node_id = next_edge.target
        run_state.current_node_id = current_node_id

    else:
        # Reached max_steps
        run_state.status = RunStatus.FAILED
        run_state.logs.append(
            RunLogEntry(
                node_id=current_node_id,
                state_snapshot=run_state.state.copy(),
                message="Max steps reached; aborting (possible infinite loop)",
            )
        )

    runs[run_id] = run_state
    return run_state
