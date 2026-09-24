from dataclasses import dataclass, field
from typing import Any


@dataclass
class Request:
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PlanStep:
    id: str
    description: str
    skill: str | None = None
    tool: str | None = None
    risk: str = "low"


@dataclass
class Plan:
    goal: str
    steps: list[PlanStep]


@dataclass
class ExecutionResult:
    success: bool
    message: str
    data: dict[str, Any] = field(default_factory=dict)
