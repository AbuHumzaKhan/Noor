from noor.models import PlanStep
from noor.permissions import PermissionPolicy


def test_high_risk_requires_confirmation() -> None:
    policy = PermissionPolicy()
    assert policy.requires_confirmation(PlanStep("1", "delete", risk="high")) is True


def test_low_risk_does_not_require_confirmation() -> None:
    policy = PermissionPolicy()
    assert policy.requires_confirmation(PlanStep("1", "inspect", risk="low")) is False
