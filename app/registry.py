# app/registry.py

from typing import Any, Awaitable, Callable, Dict, Union
import inspect


ToolFunc = Callable[[Dict[str, Any]], Dict[str, Any]]
AsyncToolFunc = Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]
ToolType = Union[ToolFunc, AsyncToolFunc]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, ToolType] = {}

    def register(self, name: str, func: ToolType) -> None:
        self._tools[name] = func

    def get(self, name: str) -> ToolType:
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not found in registry")
        return self._tools[name]

    async def run_tool(self, name: str, state: Dict[str, Any]) -> Dict[str, Any]:
        func = self.get(name)
        if inspect.iscoroutinefunction(func):
            result = await func(state)
        else:
            result = func(state)

        if not isinstance(result, dict):
            raise ValueError("Tool must return a dict to merge into state")

        return result


# Global registry instance
tool_registry = ToolRegistry()
