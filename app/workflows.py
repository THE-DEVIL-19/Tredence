# app/workflows.py

from typing import Any, Dict
import re

from .registry import tool_registry
from .models import GraphDefinition, NodeDefinition, EdgeDefinition
from .storage import graphs


# --------- Example tools for a "Code Review Mini-Agent" --------- #

def tool_extract_functions(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Very naive function extractor: looks for 'def name(' patterns.
    """
    code = state.get("code", "")
    functions = re.findall(r"def\s+(\w+)\s*\(", code)
    return {
        "functions": functions,
        "function_count": len(functions),
    }


def tool_check_complexity(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Naive complexity heuristic: count if/for/while occurrences.
    """
    code = state.get("code", "")
    complexity = (
        code.count("if ") +
        code.count("for ") +
        code.count("while ")
    )
    return {
        "complexity_score": complexity,
    }


def tool_detect_basic_issues(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simple style / formatting checks.
    """
    code = state.get("code", "")
    issues = []

    if "\t" in code:
        issues.append("Contains tab characters; prefer spaces.")
    if code.endswith(" "):
        issues.append("File ends with trailing whitespace.")
    if "print(" in code and "logging" not in code:
        issues.append("Uses print statements; consider using logging.")

    return {
        "issues": issues,
        "issue_count": len(issues),
    }


def tool_suggest_improvements(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build suggestions and compute a crude quality_score.
    Higher is better; threshold is configurable via state['threshold'].
    """
    suggestions = []

    complexity = state.get("complexity_score", 0)
    issue_count = state.get("issue_count", 0)
    function_count = state.get("function_count", 0)

    if complexity > 10:
        suggestions.append("Break complex logic into smaller functions.")
    if issue_count > 0:
        suggestions.append("Address the reported style/formatting issues.")
    if function_count == 0:
        suggestions.append("Consider structuring code into separate functions.")

    # Simple heuristic: start at 100 and subtract penalties
    quality_score = max(0, 100 - complexity * 5 - issue_count * 10)

    return {
        "suggestions": suggestions,
        "quality_score": quality_score,
    }


# --------- Setup helpers --------- #

def register_default_tools() -> None:
    """
    Register all sample tools into the global tool registry.
    """
    tool_registry.register("extract_functions", tool_extract_functions)
    tool_registry.register("check_complexity", tool_check_complexity)
    tool_registry.register("detect_basic_issues", tool_detect_basic_issues)
    tool_registry.register("suggest_improvements", tool_suggest_improvements)


def create_example_code_review_graph() -> None:
    """
    Create and register a sample graph that:
      1. Extracts functions
      2. Checks complexity
      3. Detects issues
      4. Suggests improvements
      5. Loops back to complexity if quality_score < threshold
    """
    graph = GraphDefinition(
        id="code_review_graph",
        nodes=[
            NodeDefinition(id="extract", tool_name="extract_functions"),
            NodeDefinition(id="complexity", tool_name="check_complexity"),
            NodeDefinition(id="issues", tool_name="detect_basic_issues"),
            NodeDefinition(id="suggest", tool_name="suggest_improvements"),
        ],
        edges=[
            EdgeDefinition(source="extract", target="complexity"),
            EdgeDefinition(source="complexity", target="issues"),
            EdgeDefinition(source="issues", target="suggest"),
            # Loop: if quality_score < threshold, go back to complexity
            EdgeDefinition(
                source="suggest",
                target="complexity",
                condition="state.get('quality_score', 0) < state.get('threshold', 80)",
            ),
        ],
        start_node_id="extract",
    )
    graphs[graph.id] = graph
