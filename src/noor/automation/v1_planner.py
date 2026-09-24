from __future__ import annotations

from .orchestra import TaskGraph, TaskNode


class V1Planner:
    """Deterministic planner for common Excel requests in V1.

    This is deliberately conservative: unknown requests fail closed instead of
    inventing an unsafe workflow. A future language model can produce the same
    TaskGraph contract after policy validation.
    """

    def plan_excel_analysis(self, path: str) -> TaskGraph:
        return TaskGraph(
            nodes=[
                TaskNode("excel.inspect", "excel.inspect", {"path": path}),
                TaskNode("data.profile", "data.profile", {"path": path}, ("excel.inspect",)),
                TaskNode("result.verify", "result.verify", {"capability": "data.profile"}, ("data.profile",)),
            ]
        )

    def plan_excel_inspection(self, path: str) -> TaskGraph:
        return TaskGraph(
            nodes=[
                TaskNode("excel.inspect", "excel.inspect", {"path": path}),
                TaskNode("result.verify", "result.verify", {"capability": "excel.inspect"}, ("excel.inspect",)),
            ]
        )

    def plan_excel_read(self, path: str, sheet_name: str) -> TaskGraph:
        return TaskGraph(
            nodes=[
                TaskNode(
                    "excel.read",
                    "excel.read",
                    {"path": path, "sheet_name": sheet_name},
                ),
                TaskNode("result.verify", "result.verify", {"capability": "excel.read"}, ("excel.read",)),
            ]
        )

    def plan(self, request: str, path: str, sheet_name: str | None = None) -> TaskGraph:
        """Map a small set of explicit V1 Excel intents to a validated graph."""
        text = request.casefold().strip()
        if not text:
            raise ValueError("request cannot be empty")

        if any(term in text for term in ("analyze", "analysis", "profile", "profiling")):
            return self.plan_excel_analysis(path)
        if any(term in text for term in ("read", "show", "inspect", "open")):
            if not sheet_name:
                return self.plan_excel_inspection(path)
            return self.plan_excel_read(path, sheet_name)

        raise ValueError(f"Unsupported V1 Excel request: {request}")
