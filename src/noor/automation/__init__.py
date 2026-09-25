"""Noor automation engine.

The automation package turns natural-language or structured requests into
validated, observable, composable workflows.
"""

from .data_ecosystem import DataEcosystem, DataEcosystemSkill
from .models import AutomationRequest, AutomationResult, TaskSpec
from .registry import TaskRegistry, default_registry
from .runner import AutomationRunner

__all__ = [
    "AutomationRequest",
    "AutomationResult",
    "AutomationRunner",
    "DataEcosystem",
    "DataEcosystemSkill",
    "TaskRegistry",
    "TaskSpec",
    "default_registry",
]
