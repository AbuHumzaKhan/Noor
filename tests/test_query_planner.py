from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from noor.automation.excel_query_engine import ExcelQueryEngine
from noor.automation.excel_query_planner import ExcelQueryPlanner


class QueryPlannerTests(unittest.TestCase):
    def setUp(self) -> None:
        handle = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8")
        self.path = handle.name
        with handle:
            writer = csv.writer(handle)
            writer.writerow(["City", "Service_Cost", "Brand", "Year"])
            writer.writerows([
                ["Lucknow", 100, "A", 2024],
                ["Lucknow", 150, "B", 2024],
                ["Mumbai", 80, "A", 2025],
                ["Mumbai", 120, "C", 2025],
                ["Delhi", 200, "A", 2025],
            ])

    def tearDown(self) -> None:
        Path(self.path).unlink(missing_ok=True)

    def test_group_aggregate_plan(self) -> None:
        import pandas as pd
        frame = pd.read_csv(self.path)
        plan = ExcelQueryPlanner().plan("Tell me city wise service cost", frame)
        self.assertEqual(plan.intent, "group_aggregate")
        self.assertEqual(plan.dimensions, ["City"])
        self.assertEqual(plan.measure, "Service_Cost")
        self.assertEqual(plan.aggregation, "sum")
        self.assertGreaterEqual(plan.confidence, 0.8)

    def test_top_n_plan(self) -> None:
        import pandas as pd
        frame = pd.read_csv(self.path)
        plan = ExcelQueryPlanner().plan("top 2 cities by service cost", frame)
        self.assertEqual(plan.intent, "rank")
        self.assertEqual(plan.limit, 2)
        self.assertEqual(plan.measure, "Service_Cost")

    def test_scalar_execution_uses_plan(self) -> None:
        result = ExcelQueryEngine().answer(self.path, "What is the total service cost?")
        self.assertEqual(result["resolved_query"]["intent"], "scalar_aggregate")
        self.assertEqual(result["evidence"]["value"], 650.0)
        self.assertTrue(result["verified"])

    def test_group_execution_reconciles_total(self) -> None:
        result = ExcelQueryEngine().answer(self.path, "Tell me city wise service cost")
        rows = {row["City"]: row["Service_Cost"] for row in result["evidence"]}
        self.assertEqual(rows, {"Delhi": 200, "Lucknow": 250, "Mumbai": 200})
        self.assertTrue(result["verification"]["passed"])

    def test_capability_plan(self) -> None:
        import pandas as pd
        frame = pd.read_csv(self.path)
        plan = ExcelQueryPlanner().plan("Tell me what I can do with this dataset", frame)
        self.assertEqual(plan.intent, "capability_discovery")


if __name__ == "__main__":
    unittest.main()
