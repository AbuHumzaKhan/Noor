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
    registry.register(TaskSpec("data.profile", "Profile a tabular dataset.",
                               "noor.automation.tasks.data_profiling:profile_data", "analytics",
                               ("read_data", "compute_statistics")), profile_data)
    registry.register(TaskSpec("excel.inspect", "Inspect an Excel workbook.",
                               "noor.automation.excel_skill:ExcelSkill.inspect", "excel",
                               ("read_workbook",)), excel.inspect)
    registry.register(TaskSpec("excel.read", "Read a bounded worksheet region.",
                               "noor.automation.excel_skill:ExcelSkill.read_sheet", "excel",
                               ("read_workbook", "read_data")),
                      lambda c: excel.read_sheet(str(c["path"]), str(c["sheet_name"]),
                                                 int(c.get("max_rows", ExcelSkill.DEFAULT_MAX_ROWS)),
                                                 int(c.get("max_columns", ExcelSkill.DEFAULT_MAX_COLUMNS))))
    registry.register(TaskSpec("excel.write", "Write explicit cell values or formulas.",
                               "noor.automation.excel_skill:ExcelSkill.write_cells", "excel",
                               ("write_workbook",)),
                      lambda c: excel.write_cells(str(c["path"]), str(c["sheet_name"]), dict(c["cells"]),
                                                  str(c["output_path"]) if c.get("output_path") else None))
    registry.register(TaskSpec("excel.formula.generate", "Generate an allow-listed Excel formula.",
                               "noor.automation.excel_skill:ExcelSkill.generate_formula", "excel",
                               ("generate_formula",)),
                      lambda c: excel.generate_formula(str(c["operation"]), str(c["range_ref"]),
                                                       criteria=c.get("criteria"), true_value=c.get("true_value"),
                                                       false_value=c.get("false_value")))
    registry.register(TaskSpec("excel.transform", "Apply a deterministic workbook transformation.",
                               "noor.automation.excel_skill:ExcelSkill.transform_sheet", "excel",
                               ("write_workbook", "transform_data")),
                      lambda c: excel.transform_sheet(str(c["path"]), str(c["sheet_name"]),
                                                      str(c["operation"]),
                                                      str(c["output_path"]) if c.get("output_path") else None,
                                                      column=c.get("column"), value=c.get("value"),
                                                      new_name=c.get("new_name")))
    registry.register(TaskSpec("excel.analyze", "Calculate descriptive analytics for a worksheet.",
                               "noor.automation.excel_skill:ExcelSkill.analyze_sheet", "excel",
                               ("read_data", "compute_statistics")),
                      lambda c: excel.analyze_sheet(str(c["path"]), str(c["sheet_name"])))
    registry.register(TaskSpec("result.verify", "Structurally verify a previous task output.",
                               "noor.automation.verification:verify_result", "verification",
                               ("verify_result",)),
                      lambda c: verify_result(str(c["capability"]), dict(c.get(c["capability"], {}))))
    return registry
