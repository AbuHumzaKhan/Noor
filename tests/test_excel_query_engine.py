from __future__ import annotations

import csv
import tempfile
from pathlib import Path

from noor.automation.excel_query_engine import ExcelQueryEngine
from noor.automation.v1_planner import V1Planner


def _dataset() -> str:
    handle = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8")
    with handle:
        writer = csv.writer(handle)
        writer.writerow(["City", "Service_Cost", "Brand"])
        writer.writerows([
            ["Lucknow", 100, "A"],
            ["Lucknow", 150, "B"],
            ["Mumbai", 80, "A"],
            ["Mumbai", 120, "C"],
            ["Delhi", 200, "A"],
        ])
    return handle.name


def test_city_wise_service_cost() -> None:
    path = _dataset()
    try:
        result = ExcelQueryEngine().answer(path, "Tell me city wise service cost")
        rows = {row["City"]: row["Service_Cost"] for row in result["evidence"]}
        assert rows == {"Delhi": 200, "Lucknow": 250, "Mumbai": 200}
        assert result["resolved_query"]["intent"] == "group_aggregate"
        assert result["verified"] is True
    finally:
        Path(path).unlink(missing_ok=True)


def test_planner_routes_natural_group_question() -> None:
    graph = V1Planner().plan("Tell me city wise service cost", "/tmp/service.csv")
    assert graph.nodes[0].capability == "excel.intelligence.answer"
    assert graph.nodes[0].inputs["question"] == "Tell me city wise service cost"


def test_capability_discovery() -> None:
    path = _dataset()
    try:
        result = ExcelQueryEngine().answer(path, "Tell me what I can do with this dataset")
        assert result["resolved_query"]["intent"] == "capability_discovery"
        assert result["evidence"]["numeric_columns"] == ["Service_Cost"]
    finally:
        Path(path).unlink(missing_ok=True)
