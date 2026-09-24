"""Unified orchestration for Noor's external capability providers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..models import AutomationRequest, AutomationResult
from ..registry import TaskRegistry, default_registry
from .manifest import PROVIDERS, providers_for


@dataclass(frozen=True)
class Responsibility:
    capability: str
    providers: tuple[str, ...]
    execution_owner: str
    verification_required: bool = True


class AutomationOrchestra:
    """Give heterogeneous capability providers one Noor-owned control plane.

    Providers never decide what the system should execute. Noor owns planning,
    task selection, policy boundaries, execution order, and verification.
    """

    def __init__(self, registry: TaskRegistry | None = None) -> None:
        self.registry = registry or default_registry()

    def responsibilities(self) -> tuple[Responsibility, ...]:
        capabilities = sorted({capability for provider in PROVIDERS for capability in provider.capabilities})
        return tuple(
            Responsibility(
                capability=capability,
                providers=tuple(provider.name for provider in providers_for(capability)),
                execution_owner="noor.orchestra",
            )
            for capability in capabilities
        )

    def plan(self, request: AutomationRequest) -> list[str]:
        """Build a deterministic task sequence from explicitly requested tasks.

        Natural-language planning can be added later. The current contract
        prevents an unreviewed provider from silently executing arbitrary work.
        """
        if request.requested_tasks:
            return list(request.requested_tasks)
        return []

    def execute(self, request: AutomationRequest) -> AutomationResult:
        planned_tasks = self.plan(request)
        if not planned_tasks:
            return AutomationResult(
                success=False,
                status="needs_planning",
                errors=["No executable task plan was supplied."],
                warnings=["Natural-language planning is intentionally not enabled yet."],
            )

        # Delegate actual execution to Noor's allow-listed registry.
        from ..runner import AutomationRunner

        runner = AutomationRunner(self.registry)
        return runner.run(
            AutomationRequest(
                command=request.command,
                inputs=request.inputs,
                requested_tasks=tuple(planned_tasks),
                dry_run=request.dry_run,
                metadata=request.metadata,
            )
        )

    def capability_map(self) -> dict[str, dict[str, Any]]:
        """Return the unified responsibility map used by planning and audit tooling."""
        result: dict[str, dict[str, Any]] = {}
        for responsibility in self.responsibilities():
            result[responsibility.capability] = {
                "providers": responsibility.providers,
                "execution_owner": responsibility.execution_owner,
                "verification_required": responsibility.verification_required,
            }
        return result
