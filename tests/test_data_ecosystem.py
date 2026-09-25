import unittest

from noor.automation.data_ecosystem import DataEcosystem, DataEcosystemSkill


class DataEcosystemTests(unittest.TestCase):
    def test_catalog_contains_selected_engines(self):
        names = {item["name"] for item in DataEcosystem().catalog()}
        self.assertEqual(
            names,
            {"pandas", "duckdb", "polars", "great_expectations", "apache_superset"},
        )

    def test_sql_task_prefers_duckdb_when_available(self):
        ecosystem = DataEcosystem()
        if "duckdb" not in ecosystem.available():
            self.skipTest("duckdb is not installed in this environment")
        self.assertEqual(ecosystem.select(task="run a SQL query", sql=True), "duckdb")

    def test_validation_prefers_great_expectations_when_available(self):
        ecosystem = DataEcosystem()
        if "great_expectations" not in ecosystem.available():
            self.skipTest("great_expectations is not installed in this environment")
        self.assertEqual(ecosystem.select(task="validate data quality", validation=True), "great_expectations")

    def test_large_workload_can_select_polars(self):
        ecosystem = DataEcosystem()
        if "polars" not in ecosystem.available():
            self.skipTest("polars is not installed in this environment")
        self.assertEqual(ecosystem.select(task="analyze large dataset", rows=2_000_000), "polars")

    def test_default_selection_is_pandas(self):
        self.assertEqual(DataEcosystem().select(task="profile this dataset"), "pandas")

    def test_write_sql_is_blocked(self):
        with self.assertRaises(ValueError):
            DataEcosystemSkill().execute_sql("DROP TABLE __NOOR_SOURCE__", "data.parquet")


if __name__ == "__main__":
    unittest.main()
