from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .models import TaskSpec

TaskHandler = Callable[[dict[str, Any]], dict[str, Any]]


class TaskRegistry:
    """Explicit allow-list of tasks available to the automation engine."""

    def __init__(self) -> None:
        self._specs: dict[str, TaskSpec] = {}
        self._handlers: dict[str, TaskHandler] = {}

    def register(self, spec: TaskSpec, handler: TaskHandler) -> None:
        if spec.name in self._specs:
            raise ValueError(f"Task already registered: {spec.name}")
        self._specs[spec.name] = spec
        self._handlers[spec.name] = handler

    def get(self, name: str) -> tuple[TaskSpec, TaskHandler]:
        try:
            return self._specs[name], self._handlers[name]
        except KeyError as exc:
            raise KeyError(f"Unknown automation task: {name}") from exc

    def list(self) -> tuple[TaskSpec, ...]:
        return tuple(self._specs.values())


def default_registry() -> TaskRegistry:
    """Build the safe default registry.

    Task implementations are imported lazily so the core engine remains
    usable without analytics dependencies installed.
    """

    registry = TaskRegistry()
    from .tasks.data_profiling import profile_data

    registry.register(
        TaskSpec(
            name="data.profile",
            description="Profile a tabular dataset for schema, missingness, uniqueness, and distributions.",
            handler="noor.automation.tasks.data_profiling:profile_data",
            category="analytics",
            capabilities=("read_data", "compute_statistics"),
        ),
        profile_data,
    )
    return registry
