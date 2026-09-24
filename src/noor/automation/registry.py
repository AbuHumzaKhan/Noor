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
    """Build the safe default registry with analytics, ingestion and Excel capabilities."""
    registry = TaskRegistry()
    from .data_ingest import DataIngestSkill
    from .excel_advanced import AdvancedExcelSkill
    from .excel_skill import ExcelSkill
    from .tasks.data_profiling import profile_data

    ingest = DataIngestSkill()
    excel = ExcelSkill()
    advanced = AdvancedExcelSkill()
    registry.register(TaskSpec("data.inspect", "Inspect a supported dataset file.",
                               "noor.automation.data_ingest:DataIngestSkill.inspect", "analytics",
                               ("read_data",)),
                      lambda c: ingest.inspect(str(c["path"])))
    registry.register(TaskSpec("data.load", "Load a bounded supported dataset into tabular records.",
                               "noor.automation.data_ingest:DataIngestSkill.load", "analytics",
                               ("read_data",)),
                      lambda c: ingest.load(str(c["path"]),
                                            sheet_name=str(c["sheet_name"]) if c.get("sheet_name") else None,
                                            nrows=int(c.get("nrows", 1000))))
    registry.register(TaskSpec("data.profile", "Profile a tabular dataset.",
                               "noor.automation.tasks.data_profiling:profile_data", "analytics",
                               ("read_data", "compute_statistics")), profile_data)
    registry.register(TaskSpec("excel.inspect", "Inspect an Excel workbook.",
                               "noor.automation.excel_skill:ExcelSkill.inspect", "excel",
                               ("read_workbook",)),
                      lambda c: excel.inspect(str(c["path"])))
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
    registry.register(TaskSpec("excel.summary", "Summarize workbook structure and worksheet settings.",
                               "noor.automation.excel_advanced:AdvancedExcelSkill.workbook_summary", "excel",
                               ("read_workbook",)), lambda c: advanced.workbook_summary(str(c["path"])))
    registry.register(TaskSpec("excel.search", "Search workbook cells for text.",
                               "noor.automation.excel_advanced:AdvancedExcelSkill.search", "excel",
                               ("read_workbook",)), lambda c: advanced.search(str(c["path"]), str(c["query"]), c.get("sheet_name"), int(c.get("limit", 100))))
    registry.register(TaskSpec("excel.create_sheet", "Create a worksheet.",
                               "noor.automation.excel_advanced:AdvancedExcelSkill.create_sheet", "excel",
                               ("write_workbook",)), lambda c: advanced.create_sheet(str(c["path"]), str(c["sheet_name"]), c.get("output_path")))
    registry.register(TaskSpec("excel.rename_sheet", "Rename a worksheet.",
                               "noor.automation.excel_advanced:AdvancedExcelSkill.rename_sheet", "excel",
                               ("write_workbook",)), lambda c: advanced.rename_sheet(str(c["path"]), str(c["sheet_name"]), str(c["new_name"]), c.get("output_path")))
    registry.register(TaskSpec("excel.freeze", "Freeze worksheet panes.",
                               "noor.automation.excel_advanced:AdvancedExcelSkill.freeze", "excel",
                               ("write_workbook",)), lambda c: advanced.freeze(str(c["path"]), str(c["sheet_name"]), str(c["cell"]), c.get("output_path")))
    registry.register(TaskSpec("excel.filter", "Set an AutoFilter range.",
                               "noor.automation.excel_advanced:AdvancedExcelSkill.set_filter", "excel",
                               ("write_workbook",)), lambda c: advanced.set_filter(str(c["path"]), str(c["sheet_name"]), str(c["cell_range"]), c.get("output_path")))
    registry.register(TaskSpec("excel.sort", "Sort worksheet rows by a column.",
                               "noor.automation.excel_advanced:AdvancedExcelSkill.sort_by_column", "excel",
                               ("write_workbook", "transform_data")), lambda c: advanced.sort_by_column(str(c["path"]), str(c["sheet_name"]), str(c["column"]), c.get("output_path"), bool(c.get("descending", False))))
    registry.register(TaskSpec("excel.formula.validate", "Validate basic Excel formula syntax and blocked functions.",
                               "noor.automation.excel_advanced:AdvancedExcelSkill.validate_formula", "excel",
                               ("validate_formula",)), lambda c: advanced.validate_formula(str(c["formula"])))
    registry.register(TaskSpec("excel.formula.explain", "Explain an Excel formula.",
                               "noor.automation.excel_advanced:AdvancedExcelSkill.explain_formula", "excel",
                               ("explain_formula",)), lambda c: advanced.explain_formula(str(c["formula"])))
    registry.register(TaskSpec("result.verify", "Structurally verify a previous task output.",
                               "noor.automation.verification:verify_result", "verification",
                               ("verify_result",)), lambda c: verify_result(str(c["capability"]), dict(c.get(c["capability"], {}))))
    return registry
