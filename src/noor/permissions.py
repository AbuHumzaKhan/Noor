"""Permission policy boundary for material-risk actions."""

from .models import PlanStep


class PermissionPolicy:
    def requires_confirmation(self, step: PlanStep) -> bool:
        return step.risk in {"high", "critical"}
