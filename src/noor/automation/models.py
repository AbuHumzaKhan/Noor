from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class TaskSpec:
    """Description of one executable automation task."""

    name: str
    description: str
    handler: str
    category: str
    version: str = "1.0"
    capabilities: tuple[str, ...] = ()


@dataclass(frozen=True)
class AutomationRequest:
    """Normalized request passed to the automation engine."""

    command: str
    inputs: Mapping[str, Any] = field(default_factory=dict)
    requested_tasks: tuple[str, ...] = ()
    dry_run: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass
class AutomationResult:
    """Machine-readable result with trace information."""

    success: bool
    status: str
    outputs: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    executed_tasks: list[str] = field(default_factory=list)
    trace: list[dict[str, Any]] = field(default_factory=list)
