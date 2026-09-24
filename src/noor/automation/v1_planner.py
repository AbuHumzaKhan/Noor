from __future__ import annotations

from .orchestra import TaskGraph, TaskNode


class V1Planner:
    """Deterministic planner for the first production-oriented Excel skill."""

    @staticmethod
    def _verified(capability: str, depends_on: str) -> TaskNode:
        return TaskNode("result.verify", "result.verify", {"capability": capability}, (depends_on,))

    def plan_excel_analysis(self, path: str, sheet_name: str | None = None) -> TaskGraph:
        nodes = [TaskNode("excel.inspect", "excel.inspect", {"path": path})]
        if sheet_name:
            nodes.append(TaskNode("excel.analyze", "excel.analyze",
                                  {"path": path, "sheet_name": sheet_name}, ("excel.inspect",)))
            nodes.append(self._verified("excel.analyze", "excel.analyze"))
        else:
            nodes.append(TaskNode("data.profile", "data.profile", {"path": path}, ("excel.inspect",)))
            nodes.append(self._verified("data.profile", "data.profile"))
        return TaskGraph(nodes=nodes)

    def plan_excel_inspection(self, path: str) -> TaskGraph:
        return TaskGraph(nodes=[
            TaskNode("excel.inspect", "excel.inspect", {"path": path}),
            self._verified("excel.inspect", "excel.inspect"),
        ])

    def plan_excel_read(self, path: str, sheet_name: str) -> TaskGraph:
        return TaskGraph(nodes=[
            TaskNode("excel.read", "excel.read", {"path": path, "sheet_name": sheet_name}),
            self._verified("excel.read", "excel.read"),
        ])

    def plan_excel_formula(
        self, operation: str, range_ref: str, *, criteria: str | None = None,
        true_value: object = None, false_value: object = None,
    ) -> TaskGraph:
        return TaskGraph(nodes=[
            TaskNode("excel.formula.generate", "excel.formula.generate", {
                "operation": operation, "range_ref": range_ref, "criteria": criteria,
                "true_value": true_value, "false_value": false_value,
            }),
            self._verified("excel.formula.generate", "excel.formula.generate"),
        ])

    def plan_excel_transform(
        self, path: str, sheet_name: str, operation: str, output_path: str | None = None,
        *, column: str | None = None, value: object = None, new_name: str | None = None,
    ) -> TaskGraph:
        return TaskGraph(nodes=[
            TaskNode("excel.transform", "excel.transform", {
                "path": path, "sheet_name": sheet_name, "operation": operation,
                "output_path": output_path, "column": column, "value": value, "new_name": new_name,
            }),
            self._verified("excel.transform", "excel.transform"),
        ])

    def plan(self, request: str, path: str, sheet_name: str | None = None) -> TaskGraph:
        """Map explicit V1 Excel intents to validated task graphs."""
        text = request.casefold().strip()
        if not text:
            raise ValueError("request cannot be empty")
        if any(term in text for term in ("analyze", "analysis", "profile", "profiling")):
            return self.plan_excel_analysis(path, sheet_name)
        if any(term in text for term in ("formula", "sum", "average", "count")):
            raise ValueError("Use plan_excel_formula with an explicit formula operation and range")
        if any(term in text for term in ("clean", "duplicate", "fill blank", "rename")):
            raise ValueError("Use plan_excel_transform with an explicit transformation")
        if any(term in text for term in ("read", "show", "inspect", "open")):
            return self.plan_excel_inspection(path) if not sheet_name else self.plan_excel_read(path, sheet_name)
        raise ValueError(f"Unsupported V1 Excel request: {request}")
