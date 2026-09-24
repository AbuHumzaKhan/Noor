from __future__ import annotations

from time import perf_counter
from typing import Any

from .models import AutomationRequest, AutomationResult
from .registry import TaskRegistry, default_registry


class AutomationRunner:
    """Execute a validated sequence of registered automation tasks."""

    def __init__(self, registry: TaskRegistry | None = None) -> None:
        self.registry = registry or default_registry()

    def run(self, request: AutomationRequest) -> AutomationResult:
        task_names = request.requested_tasks or self._infer_initial_tasks(request.command)
        result = AutomationResult(success=True, status="completed")
        context: dict[str, Any] = dict(request.inputs)

        for task_name in task_names:
            started = perf_counter()
            try:
                spec, handler = self.registry.get(task_name)
                if request.dry_run:
                    result.outputs[task_name] = {"dry_run": True, "task": spec.name}
                else:
                    output = handler(context)
                    result.outputs[task_name] = output
                    context.update(output)
                result.executed_tasks.append(task_name)
                result.trace.append(
                    {
                        "task": task_name,
                        "status": "skipped" if request.dry_run else "completed",
                        "duration_ms": round((perf_counter() - started) * 1000, 3),
                    }
                )
            except Exception as exc:  # boundary: preserve task failure as structured output
                result.success = False
                result.status = "failed"
                result.errors.append(f"{task_name}: {exc}")
                result.trace.append(
                    {
                        "task": task_name,
                        "status": "failed",
                        "duration_ms": round((perf_counter() - started) * 1000, 3),
                    }
                )
                break

        return result

    @staticmethod
    def _infer_initial_tasks(command: str) -> tuple[str, ...]:
        normalized = command.lower()
        if any(term in normalized for term in ("profile", "profiling", "inspect dataset")):
            return ("data.profile",)
        raise ValueError(
            "No automation plan is registered for this command. "
            "Provide requested_tasks explicitly or add a planner/skill."
        )
