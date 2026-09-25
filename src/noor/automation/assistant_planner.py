from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AssistantPlan:
    """Deterministic routing plan for Noor's natural-language assistant layer."""

    domain: str
    tasks: tuple[str, ...] = ()
    confidence: float = 0.0
    reason: str = ""
    inputs: dict[str, Any] = field(default_factory=dict)
    requires_context: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "tasks": list(self.tasks),
            "confidence": round(self.confidence, 3),
            "reason": self.reason,
            "inputs": dict(self.inputs),
            "requires_context": list(self.requires_context),
        }


class AssistantPlanner:
    """Route user requests to registered Noor capabilities without executing them."""

    DATA_EXTENSIONS = {".xlsx", ".xls", ".xlsm", ".csv", ".tsv", ".parquet", ".json", ".jsonl", ".ndjson"}
    CODE_TERMS = (
        "code", "coding", "program", "programming", "python", "javascript", "typescript",
        "react", "sql", "html", "css", "bug", "debug", "error", "exception", "function",
        "class", "refactor", "implement", "algorithm", "api", "repository", "repo", "git",
    )
    ANALYSIS_TERMS = (
        "analyze", "analyse", "analysis", "dataset", "data", "excel", "spreadsheet", "csv",
        "parquet", "profile", "clean", "missing", "duplicate", "quality", "correlation",
        "trend", "kpi", "pivot", "dashboard", "revenue", "sales", "query",
    )
    LEARNING_TERMS = (
        "learn", "teach", "explain", "understand", "what is", "how does", "why does", "tutorial",
        "practice", "quiz", "concept", "example",
    )

    def plan(self, command: str, inputs: dict[str, Any] | None = None) -> AssistantPlan:
        text = str(command or "").strip()
        if not text:
            raise ValueError("Command cannot be empty")
        normalized = text.casefold()
        context = dict(inputs or {})
        source = context.get("path") or context.get("source") or context.get("dataset")
        suffix = Path(str(source)).suffix.casefold() if source else ""
        has_data = bool(source) and suffix in self.DATA_EXTENSIONS
        has_excel = suffix in {".xlsx", ".xls", ".xlsm"}

        # A supplied dataset is authoritative context: route data work before
        # generic language such as "analyze this code" can trigger coding intent.
        if has_data:
            return self._data_plan(normalized, context, has_excel)

        if any(term in normalized for term in self.CODE_TERMS):
            return AssistantPlan(
                domain="coding",
                confidence=0.90,
                reason="The request contains software-development or debugging intent.",
                inputs=context,
                requires_context=("workspace_or_code",),
            )

        if any(term in normalized for term in self.ANALYSIS_TERMS):
            return self._data_plan(normalized, context, has_excel=False)

        if any(term in normalized for term in self.LEARNING_TERMS):
            return AssistantPlan(
                domain="learning",
                confidence=0.86,
                reason="The request is primarily explanatory or educational.",
                inputs=context,
            )

        return AssistantPlan(
            domain="general",
            confidence=0.50,
            reason="No specialized registered domain was confidently detected.",
            inputs=context,
        )

    def _data_plan(self, text: str, context: dict[str, Any], has_excel: bool) -> AssistantPlan:
        source = context.get("path") or context.get("source")
        tasks: list[str] = []
        reasons: list[str] = []

        if any(term in text for term in ("quality", "missing", "duplicate", "validation", "clean")):
            tasks.append("data.profile")
            reasons.append("profile data quality")

        if any(term in text for term in ("sql", "query", "select", "join", "cte", "window function")) and source:
            tasks.append("data.sql.query")
            reasons.append("execute read-only analytical SQL")
        elif any(term in text for term in ("profile", "inspect", "schema", "structure")) and source:
            tasks.append("data.profile")
            reasons.append("inspect and profile the dataset")

        if has_excel:
            if any(term in text for term in ("formula", "lookup", "vlookup", "xlookup", "sumif", "countif")):
                tasks.append("excel.intelligence.formula")
                reasons.append("recommend an Excel formula")
            if any(term in text for term in ("pivot", "group by", "grouped", "by city", "by customer", "by category")):
                tasks.append("excel.intelligence.pivot")
                reasons.append("build a pivot-style summary")
            if any(term in text for term in ("dashboard", "kpi", "chart", "visual")):
                tasks.append("excel.intelligence.dashboard")
                reasons.append("design an evidence-based dashboard")
            if any(term in text for term in ("complete", "full", "everything", "deep analysis")):
                tasks.append("excel.intelligence.full_analysis")
                reasons.append("run the complete Excel analysis package")
            if not tasks:
                tasks.append("excel.intelligence.answer")
                reasons.append("answer the natural-language Excel question")

        if not tasks and source:
            tasks.append("data.profile")
            reasons.append("profile the supplied data source")

        unique_tasks = tuple(dict.fromkeys(tasks))
        confidence = 0.94 if unique_tasks else 0.68
        return AssistantPlan(
            domain="data_analysis",
            tasks=unique_tasks,
            confidence=confidence,
            reason="; ".join(reasons) or "The request is data-oriented but needs a more specific operation.",
            inputs=context,
            requires_context=() if source else ("dataset_path",),
        )
