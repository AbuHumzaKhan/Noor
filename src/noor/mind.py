"""Requirement understanding and high-level reasoning boundary.

The mind layer is deliberately provider-neutral. It should turn a user request
into structured intent and a candidate plan; execution remains separate.
"""

from .models import Plan, PlanStep, Request


class NoorMind:
    def understand(self, request: Request) -> str:
        return request.text.strip()

    def draft_plan(self, request: Request) -> Plan:
        goal = self.understand(request)
        return Plan(
            goal=goal,
            steps=[PlanStep(id="step-1", description="Inspect context and determine the required action.")],
        )
