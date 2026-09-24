"""Orchestration layer connecting mind, selection, permissions, execution and verification."""

from .executor import Executor
from .mind import NoorMind
from .models import ExecutionResult, Request
from .permissions import PermissionPolicy
from .selector import ToolSelector
from .verifier import Verifier


class NoorAgent:
    def __init__(self) -> None:
        self.mind = NoorMind()
        self.selector = ToolSelector()
        self.permissions = PermissionPolicy()
        self.executor = Executor()
        self.verifier = Verifier()

    def handle(self, text: str) -> ExecutionResult:
        request = Request(text=text)
        plan = self.mind.draft_plan(request)
        for step in plan.steps:
            self.selector.select(step)
            if self.permissions.requires_confirmation(step):
                return ExecutionResult(False, "Confirmation required before execution.")
            result = self.executor.execute(step)
            if not self.verifier.verify(result):
                return result
        return ExecutionResult(True, "Request processed by the Noor orchestration pipeline.")
