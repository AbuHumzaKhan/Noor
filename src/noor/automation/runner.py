from __future__ import annotations

from time import perf_counter
from typing import Any

from .assistant_planner import AssistantPlanner
from .models import AutomationRequest, AutomationResult
from .registry import TaskRegistry, default_registry


class AutomationRunner:
    """Execute validated automation tasks selected from natural-language intent."""

    def __init__(self, registry: TaskRegistry | None = None) -> None:
        self.registry = registry or default_registry()
        self.planner = AssistantPlanner()

    def run(self, request: AutomationRequest) -> AutomationResult:
        context: dict[str, Any] = dict(request.inputs)
        plan = self.planner.plan(request.command, context)
        task_names = request.requested_tasks or plan.tasks
        result = AutomationResult(success=True, status="completed")
        result.outputs["assistant.plan"] = plan.as_dict()

        if not task_names:
            result.status = "planned"
            if plan.requires_context:
                result.warnings.append(
                    "Additional context is required before Noor can execute this request: "
                    + ", ".join(plan.requires_context)
                )
            else:
                result.warnings.append("No executable registered task matched the request yet.")
            return result

        for task_name in task_names:
            started = perf_counter()
            try:
                spec, handler = self.registry.get(task_name)
                if request.dry_run:
                    result.outputs[task_name] = {"dry_run": True, "task": spec.name}
                else:
                    output = handler(context)
                    result.outputs[task_name] = output
                    if isinstance(output, dict):
                        context.update(output)
                result.executed_tasks.append(task_name)
                result.trace.append(
                    {
                        "task": task_name,
                        "status": "skipped" if request.dry_run else "completed",
                        "duration_ms": round((perf_counter() - started) * 1000, 3),
                    }
                )
            except Exception as exc:  # noqa: BLE001 - task boundary
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

    def plan(self, command: str, inputs: dict[str, Any] | None = None) -> dict[str, Any]:
        """Expose routing without executing any task; useful to the UI and tests."""
        return self.planner.plan(command, inputs).as_dict()
