from noor.automation.models import AutomationRequest, TaskSpec
from noor.automation.registry import TaskRegistry
from noor.automation.runner import AutomationRunner


def test_runner_executes_registered_task() -> None:
    registry = TaskRegistry()
    registry.register(
        TaskSpec(
            name="test.echo",
            description="Echo test input",
            handler="tests.echo",
            category="test",
        ),
        lambda context: {"echo": context["value"]},
    )

    result = AutomationRunner(registry).run(
        AutomationRequest(
            command="run test",
            inputs={"value": "ok"},
            requested_tasks=("test.echo",),
        )
    )

    assert result.success is True
    assert result.outputs["test.echo"]["echo"] == "ok"
    assert result.executed_tasks == ["test.echo"]


def test_runner_supports_dry_run() -> None:
    registry = TaskRegistry()
    registry.register(
        TaskSpec(
            name="test.echo",
            description="Echo test input",
            handler="tests.echo",
            category="test",
        ),
        lambda context: {"echo": context["value"]},
    )

    result = AutomationRunner(registry).run(
        AutomationRequest(
            command="dry run",
            inputs={"value": "ok"},
            requested_tasks=("test.echo",),
            dry_run=True,
        )
    )

    assert result.success is True
    assert result.outputs["test.echo"]["dry_run"] is True
