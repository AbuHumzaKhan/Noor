from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .models import TaskSpec
from .verification import verify_result

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
    """Build the safe default registry with analytics and Excel capabilities."""

    registry = TaskRegistry()
    from .excel_skill import ExcelSkill
    from .tasks.data_profiling import profile_data

    excel = ExcelSkill()

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
    registry.register(
        TaskSpec(
            name="excel.inspect",
            description="Inspect an Excel workbook and return worksheet dimensions.",
            handler="noor.automation.excel_skill:ExcelSkill.inspect",
            category="excel",
            capabilities=("read_workbook",),
        ),
        excel.inspect,
    )
    registry.register(
        TaskSpec(
            name="excel.read",
            description="Read a bounded worksheet region without executing workbook macros.",
            handler="noor.automation.excel_skill:ExcelSkill.read_sheet",
            category="excel",
            capabilities=("read_workbook", "read_data"),
        ),
        lambda context: excel.read_sheet(
            str(context["path"]),
            str(context["sheet_name"]),
            int(context.get("max_rows", ExcelSkill.DEFAULT_MAX_ROWS)),
            int(context.get("max_columns", ExcelSkill.DEFAULT_MAX_COLUMNS)),
        ),
    )
    registry.register(
        TaskSpec(
            name="excel.write",
            description="Write explicit cell values or formulas to an Excel workbook.",
            handler="noor.automation.excel_skill:ExcelSkill.write_cells",
            category="excel",
            capabilities=("write_workbook",),
        ),
        lambda context: excel.write_cells(
            str(context["path"]),
            str(context["sheet_name"]),
            dict(context["cells"]),
            str(context["output_path"]) if context.get("output_path") else None,
        ),
    )
    registry.register(
        TaskSpec(
            name="result.verify",
            description="Structurally verify the output of a previous automation task.",
            handler="noor.automation.verification:verify_result",
            category="verification",
            capabilities=("verify_result",),
        ),
        lambda context: verify_result(
            str(context["capability"]),
            dict(context.get(context["capability"], {})),
        ),
    )
    return registry
