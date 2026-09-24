from __future__ import annotations

import re
from pathlib import Path
from typing import ClassVar

from .orchestra import TaskGraph, TaskNode


class V1Planner:
    """Deterministic natural-language planner for Noor V1 data and Excel skills."""

    _RANGE_PATTERN = re.compile(r"\b(?:[A-Za-z]{1,3}\d+:[A-Za-z]{1,3}\d+|[A-Za-z]{1,3}:[A-Za-z]{1,3})\b")
    _FORMULA_PATTERN = re.compile(r"=\s*[A-Za-z][A-Za-z0-9_.]*\s*\([^\n]+\)")
    _EXCEL_EXTENSIONS: ClassVar[set[str]] = {".xlsx", ".xlsm", ".xltx", ".xltm", ".xls", ".ods"}

    @staticmethod
    def _verified(capability: str, depends_on: str) -> TaskNode:
        return TaskNode("result.verify", "result.verify", {"capability": capability}, (depends_on,))

    def plan_excel_analysis(self, path: str, sheet_name: str | None = None) -> TaskGraph:
        self._require_path(path)
        nodes = [TaskNode("excel.inspect", "excel.inspect", {"path": path})]
        if sheet_name:
            nodes.append(TaskNode("excel.analyze", "excel.analyze", {"path": path, "sheet_name": sheet_name}, ("excel.inspect",)))
            nodes.append(self._verified("excel.analyze", "excel.analyze"))
        else:
            nodes.append(TaskNode("data.profile", "data.profile", {"path": path}, ("excel.inspect",)))
            nodes.append(self._verified("data.profile", "data.profile"))
        return TaskGraph(nodes=nodes)

    def plan_intelligence(self, capability: str, inputs: dict[str, object]) -> TaskGraph:
        self._require_path(str(inputs.get("path", "")))
        return TaskGraph(nodes=[TaskNode(capability, capability, inputs), self._verified(capability, capability)])

    def plan_data_profile(self, path: str) -> TaskGraph:
        self._require_path(path)
        return TaskGraph(nodes=[TaskNode("data.inspect", "data.inspect", {"path": path}), TaskNode("data.profile", "data.profile", {"path": path}, ("data.inspect",)), self._verified("data.profile", "data.profile")])

    def plan_excel_inspection(self, path: str) -> TaskGraph:
        self._require_path(path)
        return TaskGraph(nodes=[TaskNode("excel.inspect", "excel.inspect", {"path": path}), self._verified("excel.inspect", "excel.inspect")])

    def plan_excel_read(self, path: str, sheet_name: str) -> TaskGraph:
        self._require_path(path)
        if not sheet_name.strip(): raise ValueError("A worksheet name is required to read Excel data")
        return TaskGraph(nodes=[TaskNode("excel.read", "excel.read", {"path": path, "sheet_name": sheet_name}), self._verified("excel.read", "excel.read")])

    def plan_excel_formula(self, operation: str, range_ref: str, *, criteria: str | None = None, true_value: object = None, false_value: object = None) -> TaskGraph:
        return TaskGraph(nodes=[TaskNode("excel.formula.generate", "excel.formula.generate", {"operation": operation, "range_ref": range_ref, "criteria": criteria, "true_value": true_value, "false_value": false_value}), self._verified("excel.formula.generate", "excel.formula.generate")])

    def plan_excel_transform(self, path: str, sheet_name: str, operation: str, output_path: str | None = None, *, column: str | None = None, value: object = None, new_name: str | None = None) -> TaskGraph:
        self._require_path(path)
        if not sheet_name.strip(): raise ValueError("A worksheet name is required for Excel transformations")
        return TaskGraph(nodes=[TaskNode("excel.transform", "excel.transform", {"path": path, "sheet_name": sheet_name, "operation": operation, "output_path": output_path, "column": column, "value": value, "new_name": new_name}), self._verified("excel.transform", "excel.transform")])

    def plan_excel_advanced(self, capability: str, inputs: dict[str, object]) -> TaskGraph:
        self._require_path(str(inputs.get("path", "")))
        return TaskGraph(nodes=[TaskNode(capability, capability, inputs), self._verified(capability, capability)])

    def plan(self, request: str, path: str | None = None, sheet_name: str | None = None) -> TaskGraph:
        text = request.casefold().strip()
        if not text: raise ValueError("request cannot be empty")
        source = Path(path).suffix.lower() if path else ""
        is_excel = source in self._EXCEL_EXTENSIONS
        has_dataset = bool(path and str(path).strip())

        if has_dataset and any(term in text for term in ("analyze complete", "analyze the complete", "full analysis", "deep analysis", "complete analysis", "analyze everything", "analyze all", "profile the complete", "profile the entire")):
            return self.plan_intelligence("excel.intelligence.full_analysis", {"path": path, "sheet_name": sheet_name})
        if has_dataset and any(term in text for term in ("which formula", "what formula", "formula should", "formula do i", "excel formula for", "recommend a formula")):
            version = self._extract_excel_version(request)
            return self.plan_intelligence("excel.intelligence.formula", {"path": path, "request": request, "sheet_name": sheet_name, "excel_version": version})
        if has_dataset and any(term in text for term in ("generate questions", "suggest questions", "what can i ask", "questions i can ask", "give me questions")):
            return self.plan_intelligence("excel.intelligence.questions", {"path": path, "sheet_name": sheet_name, "limit": 12})
        if has_dataset and any(term in text for term in ("pivot table", "pivot summary", "pivot report", "summarize by", "group by")):
            row_field = self._extract_group_field(request, path)
            value_field = self._extract_value_field(request, path)
            column_field = self._extract_column_field(request, row_field)
            if not row_field: raise ValueError("Tell me which field to group by, for example: total sales by Category")
            return self.plan_intelligence("excel.intelligence.pivot", {"path": path, "sheet_name": sheet_name, "row_field": row_field, "value_field": value_field, "column_field": column_field, "aggfunc": self._extract_aggregation(text)})
        if has_dataset and any(term in text for term in ("dashboard", "dashboarding", "kpi report", "management report", "reporting layout", "create a report")):
            return self.plan_intelligence("excel.intelligence.dashboard", {"path": path, "sheet_name": sheet_name})
        if has_dataset and any(term in text for term in ("formula catalog", "all excel formulas", "excel functions", "list formulas", "formula functions")):
            return TaskGraph(nodes=[TaskNode("excel.intelligence.formulas", "excel.intelligence.formulas", {"query": self._extract_formula_query(request)}), self._verified("excel.intelligence.formulas", "excel.intelligence.formulas")])
        if has_dataset and self._looks_like_question(text):
            return self.plan_intelligence("excel.intelligence.answer", {"path": path, "question": request, "sheet_name": sheet_name})
        if has_dataset and any(term in text for term in ("analyze", "analysis", "profile", "profiling", "trend", "insight", "data quality")):
            return self.plan_intelligence("excel.intelligence.profile", {"path": path, "sheet_name": sheet_name})

        if is_excel and any(term in text for term in ("search", "find", "lookup in workbook")):
            query = self._extract_search_query(request)
            if not query: raise ValueError("Tell me what text to search for in the workbook")
            return self.plan_excel_advanced("excel.search", {"path": path, "query": query, "sheet_name": sheet_name})
        if is_excel and "freeze" in text:
            return self.plan_excel_advanced("excel.freeze", {"path": path, "sheet_name": sheet_name or "Sheet1", "cell": self._extract_cell(request) or "A2"})
        if is_excel and any(term in text for term in ("filter", "autofilter", "auto filter")):
            cell_range = self._extract_range(request)
            if not cell_range: raise ValueError("Provide a filter range such as A1:F100")
            return self.plan_excel_advanced("excel.filter", {"path": path, "sheet_name": sheet_name or "Sheet1", "cell_range": cell_range})
        if is_excel and "sort" in text:
            return self.plan_excel_advanced("excel.sort", {"path": path, "sheet_name": sheet_name or "Sheet1", "column": self._extract_column(request) or "A", "descending": any(term in text for term in ("descending", "largest", "highest"))})
        if is_excel and "create sheet" in text:
            return self.plan_excel_advanced("excel.create_sheet", {"path": path, "sheet_name": self._extract_after(request, ("create sheet", "create worksheet")) or "NewSheet"})
        if is_excel and "rename sheet" in text:
            match = re.search(r"rename\s+(?:sheet|worksheet)\s+(.+?)\s+to\s+(.+)$", request, re.IGNORECASE)
            if not match: raise ValueError("Use: rename sheet OldName to NewName")
            return self.plan_excel_advanced("excel.rename_sheet", {"path": path, "sheet_name": match.group(1).strip(), "new_name": match.group(2).strip()})

        formula_match = self._FORMULA_PATTERN.search(request)
        if is_excel and formula_match and any(term in text for term in ("validate", "check", "is this formula")):
            return self.plan_excel_advanced("excel.formula.validate", {"formula": formula_match.group(0)})
        if is_excel and formula_match and any(term in text for term in ("explain formula", "explain this formula")):
            return self.plan_excel_advanced("excel.formula.explain", {"formula": formula_match.group(0)})
        if is_excel and any(term in text for term in ("formula", "sum", "average", "avg", "count", "minimum", "maximum")):
            range_ref = self._extract_range(request)
            if not range_ref: raise ValueError("I need a cell range, such as B2:B100, to generate the Excel formula")
            return self.plan_excel_formula(self._formula_operation(text), range_ref)
        if is_excel and any(term in text for term in ("clean", "duplicate", "fill blank", "rename header")):
            operation = self._transform_operation(text)
            return self.plan_excel_transform(path or "", sheet_name or "", operation, column=self._extract_column(request) if operation in {"fill_blank", "rename_header"} else None, value=self._extract_fill_value(request) if operation == "fill_blank" else None, new_name=self._extract_rename_value(request) if operation == "rename_header" else None)
        if is_excel and any(term in text for term in ("read", "show", "inspect", "open", "workbook", "worksheet")):
            return self.plan_excel_read(path or "", sheet_name) if sheet_name else self.plan_excel_inspection(path or "")
        if path and any(term in text for term in ("inspect", "profile", "analyze", "load", "read", "show")):
            return self.plan_data_profile(path)
        raise ValueError("Unsupported V1 request. Attach a dataset and ask Noor to inspect, profile, analyze, clean, answer questions, recommend formulas, build pivot summaries, or design reports.")

    @staticmethod
    def _require_path(path: str) -> None:
        if not path.strip(): raise ValueError("Attach a dataset or Excel workbook first")

    @staticmethod
    def _looks_like_question(text: str) -> bool:
        starters = ("what ", "how ", "which ", "where ", "when ", "who ", "is ", "are ", "can ", "show me ", "tell me ", "calculate ", "find ")
        return text.endswith("?") or text.startswith(starters) or any(term in text for term in ("total sales", "total revenue", "average", "median", "maximum", "minimum", "missing values", "duplicates", "correlation", "top 10", "top 5"))

    @staticmethod
    def _extract_excel_version(request: str) -> str:
        match = re.search(r"\b(2016|2019|2021|2024|365)\b", request)
        return match.group(1) if match else "2021"

    @staticmethod
    def _extract_aggregation(text: str) -> str:
        if "average" in text or "mean" in text: return "mean"
        if "count" in text: return "count"
        if "minimum" in text or re.search(r"\bmin\b", text): return "min"
        if "maximum" in text or re.search(r"\bmax\b", text): return "max"
        if "median" in text: return "median"
        return "sum"

    @staticmethod
    def _extract_group_field(request: str, path: str) -> str | None:
        match = re.search(r"(?:by|group\s+by|rows?)\s+['\"]?([^,?]+?)['\"]?(?:\s+(?:and|with|using)\s+|\?|$)", request, re.IGNORECASE)
        return match.group(1).strip() if match else None

    @staticmethod
    def _extract_value_field(request: str, path: str) -> str | None:
        match = re.search(r"(?:sum|total|average|mean|count|minimum|maximum|median)\s+(?:of\s+)?['\"]?([^,?]+?)['\"]?\s+(?:by|group\s+by)", request, re.IGNORECASE)
        return match.group(1).strip() if match else None

    @staticmethod
    def _extract_column_field(request: str, row_field: str | None) -> str | None:
        match = re.search(r"(?:columns?|across)\s+['\"]?([^,?]+?)['\"]?(?:\?|$)", request, re.IGNORECASE)
        return match.group(1).strip() if match and match.group(1).strip() != (row_field or "") else None

    @staticmethod
    def _extract_formula_query(request: str) -> str | None:
        match = re.search(r"(?:about|for|category)\s+(.+)$", request, re.IGNORECASE)
        return match.group(1).strip() if match else None

    @staticmethod
    def _formula_operation(text: str) -> str:
        if "average" in text or "avg" in text: return "average"
        if "count" in text: return "count"
        if "minimum" in text or re.search(r"\bmin\b", text): return "min"
        if "maximum" in text or re.search(r"\bmax\b", text): return "max"
        return "sum"

    @classmethod
    def _extract_range(cls, request: str) -> str | None:
        match = cls._RANGE_PATTERN.search(request)
        return match.group(0) if match else None

    @staticmethod
    def _extract_cell(request: str) -> str | None:
        match = re.search(r"\b([A-Za-z]{1,3}[1-9][0-9]*)\b", request)
        return match.group(1).upper() if match else None

    @staticmethod
    def _transform_operation(text: str) -> str:
        if "duplicate" in text: return "remove_duplicates"
        if "fill blank" in text: return "fill_blank"
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

    @staticmethod
    def _extract_after(request: str, prefixes: tuple[str, ...]) -> str | None:
        lowered = request.casefold()
        for prefix in prefixes:
            index = lowered.find(prefix.casefold())
            if index >= 0:
                value = request[index + len(prefix):].strip(" :.-")
                if value: return value
        return None

    @staticmethod
    def _extract_search_query(request: str) -> str | None:
        match = re.search(r"(?:search|find)\s+(?:this\s+)?(?:workbook|sheet)?\s*(?:for|:)?\s*(.+)$", request, re.IGNORECASE)
        if match: return match.group(1).strip()
        return V1Planner._extract_after(request, ("lookup in workbook",))
