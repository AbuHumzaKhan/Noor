from pathlib import Path

import pytest

from noor.automation.data_ingest import DataIngestSkill
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
