from __future__ import annotations

from .orchestra import TaskGraph, TaskNode


class V1Planner:
    """Small deterministic planner for the first Excel workflow.

    Natural-language planning can replace/extend this component later. Keeping
    the graph explicit makes provider selection and verification testable.
    """

    def plan_excel_analysis(self, path: str) -> TaskGraph:
        return TaskGraph(nodes=[
            TaskNode("excel.inspect", "excel.inspect", {"path": path}),
            TaskNode("data.profile", "data.profile", depends_on=("excel.inspect",)),
            TaskNode("result.verify", "result.verify", depends_on=("data.profile",)),
        ])
