from dataclasses import dataclass
from typing import Any


@dataclass
class WorkflowStepResult:
    step_name: str
    tool_name: str
    status: str
    arguments: dict[str, Any] | None = None
    result: Any = None
    error: str | None = None


@dataclass
class WorkflowResult:
    workflow_name: str
    status: str
    steps: list[WorkflowStepResult]
    output: Any = None
    error: str | None = None