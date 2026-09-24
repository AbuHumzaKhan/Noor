"""Post-execution verification boundary."""

from .models import ExecutionResult


class Verifier:
    def verify(self, result: ExecutionResult) -> bool:
        return result.success
