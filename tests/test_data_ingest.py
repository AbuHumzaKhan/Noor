from pathlib import Path

import pytest

from noor.automation.data_ingest import DataIngestSkill
from noor.automation.orchestra import TaskGraph, TaskNode, UnifiedOrchestra
from noor.automation.registry import default_registry
from noor.automation.tasks.data_profiling import profile_data


@pytest.fixture
def csv_file(tmp_path: Path) -> Path:
    path = tmp_path / "sales.csv"
    path.write_text("id,amount,region\n1,10,East\n2,20,West\n2,20,West\n", encoding="utf-8")
    return path


def test_supported_dataset_catalog_contains_25_plus_formats() -> None:
    skill = DataIngestSkill()
    assert len(skill.SUPPORTED_EXTENSIONS) >= 25
    assert {".csv", ".json", ".xml", ".parquet", ".xlsx", ".sqlite"}.issubset(skill.SUPPORTED_EXTENSIONS)


def test_inspect_csv(csv_file: Path) -> None:
    result = DataIngestSkill().inspect(str(csv_file))
    assert result["format"] == "CSV"
    assert result["bytes"] > 0


def test_load_csv(csv_file: Path) -> None:
    result = DataIngestSkill().load(str(csv_file))
    assert result["rows_returned"] == 3
    assert result["columns"] == ["id", "amount", "region"]


def test_profile_csv(csv_file: Path) -> None:
    result = profile_data({"path": str(csv_file)})
    assert result["rows"] == 3
    assert result["columns"] == 3
    assert result["duplicate_rows"] == 1


def test_orchestra_data_inspect_receives_task_context(csv_file: Path) -> None:
    registry = default_registry()
    orchestra = UnifiedOrchestra()
    _, handler = registry.get("data.inspect")
    orchestra.register_provider("data.inspect", handler)

    executions = orchestra.execute(
        TaskGraph([TaskNode("data.inspect", "data.inspect", {"path": str(csv_file)})])
    )

    assert executions[0].status == "success"
    assert executions[0].output["format"] == "CSV"
    assert executions[0].output["path"] == str(csv_file)


def test_orchestra_data_profile_pipeline(csv_file: Path) -> None:
    registry = default_registry()
    orchestra = UnifiedOrchestra()
    for capability in ("data.inspect", "data.profile", "result.verify"):
        _, handler = registry.get(capability)
        orchestra.register_provider(capability, handler)

    graph = TaskGraph([
        TaskNode("data.inspect", "data.inspect", {"path": str(csv_file)}),
        TaskNode("data.profile", "data.profile", {"path": str(csv_file)}, ("data.inspect",)),
        TaskNode("result.verify", "result.verify", {"capability": "data.profile"}, ("data.profile",)),
    ])
    executions = orchestra.execute(graph)

    assert [item.status for item in executions] == ["success", "success", "success"]
    assert executions[-1].output["valid"] is True
