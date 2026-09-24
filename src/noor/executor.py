"""Controlled execution boundary. Concrete tools will be registered separately."""

from .models import ExecutionResult, PlanStep


class Executor:
    def execute(self, step: PlanStep) -> ExecutionResult:
        return ExecutionResult(success=False, message=f"No executor registered for: {step.id}")
