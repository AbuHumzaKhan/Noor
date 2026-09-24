from __future__ import annotations

import re

from .orchestra import TaskGraph, TaskNode


class V1Planner:
    """Deterministic natural-language planner for Noor's first Excel skill."""

    _RANGE_PATTERN = re.compile(r"\b(?:[A-Za-z]{1,3}\d+:[A-Za-z]{1,3}\d+|[A-Za-z]{1,3}:[A-Za-z]{1,3})\b")

    @staticmethod
    def _verified(capability: str, depends_on: str) -> TaskNode:
        return TaskNode("result.verify", "result.verify", {"capability": capability}, (depends_on,))

    def plan_excel_analysis(self, path: str, sheet_name: str | None = None) -> TaskGraph:
        self._require_path(path)
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
        self._require_path(path)
        return TaskGraph(nodes=[
            TaskNode("excel.inspect", "excel.inspect", {"path": path}),
            self._verified("excel.inspect", "excel.inspect"),
        ])

    def plan_excel_read(self, path: str, sheet_name: str) -> TaskGraph:
        self._require_path(path)
        if not sheet_name.strip():
            raise ValueError("A worksheet name is required to read Excel data")
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
        self._require_path(path)
        if not sheet_name.strip():
            raise ValueError("A worksheet name is required for Excel transformations")
        return TaskGraph(nodes=[
            TaskNode("excel.transform", "excel.transform", {
                "path": path, "sheet_name": sheet_name, "operation": operation,
                "output_path": output_path, "column": column, "value": value, "new_name": new_name,
            }),
            self._verified("excel.transform", "excel.transform"),
        ])

    def plan(self, request: str, path: str | None = None, sheet_name: str | None = None) -> TaskGraph:
        """Map a natural-language V1 Excel request to a validated task graph."""
        text = request.casefold().strip()
        if not text:
            raise ValueError("request cannot be empty")
        if any(term in text for term in ("analyze", "analysis", "profile", "profiling", "trend", "insight")):
            return self.plan_excel_analysis(path or "", sheet_name)

        if any(term in text for term in ("formula", "sum", "average", "avg", "count", "minimum", "maximum")):
            operation = self._formula_operation(text)
            range_ref = self._extract_range(request)
            if not range_ref:
                raise ValueError("I need a cell range, such as B2:B100, to generate the Excel formula")
            return self.plan_excel_formula(operation, range_ref)

        if any(term in text for term in ("clean", "duplicate", "fill blank", "rename header")):
            self._require_path(path or "")
            operation = self._transform_operation(text)
            value = self._extract_fill_value(request) if operation == "fill_blank" else None
            new_name = self._extract_rename_value(request) if operation == "rename_header" else None
            column = self._extract_column(request) if operation in {"fill_blank", "rename_header"} else None
            return self.plan_excel_transform(path or "", sheet_name or "", operation,
                                             column=column, value=value, new_name=new_name)

        if any(term in text for term in ("read", "show", "inspect", "open", "workbook", "worksheet")):
            if sheet_name:
                return self.plan_excel_read(path or "", sheet_name)
            return self.plan_excel_inspection(path or "")

        raise ValueError("Unsupported V1 request. Try inspect, read, profile, analyze, formula, or clean an Excel workbook.")

    @staticmethod
    def _require_path(path: str) -> None:
        if not path.strip():
            raise ValueError("Attach an Excel workbook or provide its local file path first")

    @staticmethod
    def _formula_operation(text: str) -> str:
        if "average" in text or "avg" in text:
            return "average"
        if "count" in text:
            return "count"
        if "minimum" in text or re.search(r"\bmin\b", text):
            return "min"
        if "maximum" in text or re.search(r"\bmax\b", text):
            return "max"
        return "sum"

    @classmethod
    def _extract_range(cls, request: str) -> str | None:
        match = cls._RANGE_PATTERN.search(request)
        return match.group(0) if match else None

    @staticmethod
    def _transform_operation(text: str) -> str:
        if "duplicate" in text:
            return "remove_duplicates"
        if "fill blank" in text:
            return "fill_blank"
        return "rename_header"

    @staticmethod
    def _extract_column(request: str) -> str | None:
        match = re.search(r"\bcolumn\s+([A-Za-z]{1,3})\b", request, re.IGNORECASE)
        return match.group(1).upper() if match else None

    @staticmethod
    def _extract_fill_value(request: str) -> str | None:
        match = re.search(r"fill\s+(?:blank|blanks)\s+(?:with|using)\s+([^.,]+)", request, re.IGNORECASE)
        return match.group(1).strip() if match else None

    @staticmethod
    def _extract_rename_value(request: str) -> str | None:
        match = re.search(r"rename\s+(?:header|column)\s+(?:to|as)\s+([^.,]+)", request, re.IGNORECASE)
        return match.group(1).strip() if match else None
