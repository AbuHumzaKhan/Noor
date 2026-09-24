"""Dependency-aware task graph execution for Noor's automation orchestra."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class TaskNode:
    id: str
    capability: str
    inputs: dict[str, Any] = field(default_factory=dict)
    depends_on: tuple[str, ...] = ()
    retries: int = 1


@dataclass
class TaskExecution:
    node_id: str
    capability: str
    status: str
    output: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    attempts: int = 0


@dataclass
class TaskGraph:
    nodes: list[TaskNode]

    def validate(self) -> None:
        ids = {node.id for node in self.nodes}
        if len(ids) != len(self.nodes):
            raise ValueError("Task graph contains duplicate node IDs")
        for node in self.nodes:
            missing = set(node.depends_on) - ids
            if missing:
                raise ValueError(
                    f"Task {node.id} depends on unknown nodes: {sorted(missing)}"
                )


class UnifiedOrchestra:
    """Execute a Noor-owned task graph through registered providers."""

    def __init__(self) -> None:
        self._providers: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {}

    def register_provider(
        self,
        capability: str,
        handler: Callable[[dict[str, Any]], dict[str, Any]],
    ) -> None:
        if capability in self._providers:
            raise ValueError(f"Provider already registered: {capability}")
        self._providers[capability] = handler

    def execute(
        self,
        graph: TaskGraph,
        initial_context: dict[str, Any] | None = None,
    ) -> list[TaskExecution]:
        graph.validate()
        context = dict(initial_context or {})
        completed: set[str] = set()
        executions: list[TaskExecution] = []

        while len(completed) < len(graph.nodes):
            ready = [
                node
                for node in graph.nodes
                if node.id not in completed
                and set(node.depends_on).issubset(completed)
            ]
            if not ready:
                raise ValueError(
                    "Task graph contains a dependency cycle or unresolved dependency"
                )

            for node in ready:
                handler = self._providers.get(node.capability)
                if handler is None:
                    executions.append(
                        TaskExecution(
                            node.id,
                            node.capability,
                            "blocked",
                            errors=["No provider registered"],
                        )
                    )
                    raise RuntimeError(
                        f"No provider registered for capability: {node.capability}"
                    )

                payload = dict(context)
                payload.update(node.inputs)
                execution = TaskExecution(node.id, node.capability, "failed")

                for attempt in range(1, node.retries + 2):
                    execution.attempts = attempt
                    try:
                        output = handler(payload)
                        execution.status = "success"
                        execution.output = output
                        context[node.id] = output
                        completed.add(node.id)
                        break
                    except Exception as exc:  # noqa: BLE001 - provider boundary
                        execution.errors.append(str(exc))
                executions.append(execution)
                if execution.status != "success":
                    return executions

        return executions
