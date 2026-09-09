from dataclasses import dataclass
from typing import Any


@dataclass
class RouteResult:
    intent: str
    tool_name: str | None
    data: Any = None
    error: str | None = None


@dataclass
class ExecutionRecord:
    query: str
    intent: str
    tool_name: str | None
    result: Any = None
    status: str = "success"
    follow_up: bool = False