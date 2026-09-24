"""Select the least-risk capability/tool capable of fulfilling a plan step."""

from .models import PlanStep


class ToolSelector:
    def select(self, step: PlanStep) -> str | None:
        return step.tool
