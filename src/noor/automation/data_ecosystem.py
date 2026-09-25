from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class EngineCapability:
    name: str
    repository: str
    purpose: str
    capabilities: tuple[str, ...]
    optional_dependency: str | None = None
    requires_service: bool = False


ENGINES: tuple[EngineCapability, ...] = (
    EngineCapability(
        name="pandas",
        repository="pandas-dev/pandas",
        purpose="Primary Python dataframe and practical data-analysis engine.",
        capabilities=(
            "tabular analysis", "cleaning", "missing-value analysis", "groupby", "joins",
            "aggregation", "time-series", "Excel I/O", "CSV I/O", "database I/O",
        ),
    ),
    EngineCapability(
        name="duckdb",
        repository="duckdb/duckdb",
        purpose="In-process analytical SQL engine for files and relational workloads.",
        capabilities=(
            "SQL analytics", "CSV queries", "Parquet queries", "joins", "window functions",
            "aggregations", "CTEs", "nested queries", "pandas integration",
        ),
        optional_dependency="duckdb",
    ),
    EngineCapability(
        name="polars",
        repository="pola-rs/polars",
        purpose="High-performance dataframe/query engine for larger analytical workloads.",
        capabilities=(
            "lazy queries", "eager queries", "streaming", "larger-than-RAM processing",
            "multi-threaded execution", "CSV I/O", "Parquet I/O", "SQL", "expressions",
        ),
        optional_dependency="polars",
    ),
    EngineCapability(
        name="great_expectations",
        repository="great-expectations/great_expectations",
        purpose="Data-quality expectations, validation, profiling, and documentation.",
        capabilities=(
            "schema checks", "null checks", "uniqueness checks", "range checks",
            "format checks", "row-count checks", "expectation suites", "validation results",
        ),
        optional_dependency="great_expectations",
    ),
    EngineCapability(
        name="apache_superset",
        repository="apache/superset",
        purpose="BI and visualization platform used as an optional external presentation layer.",
        capabilities=(
            "SQL editor", "chart building", "dashboards", "semantic metrics", "data exploration",
            "visualization", "database connectors", "security roles", "REST API",
        ),
        requires_service=True,
    ),
)


class DataEcosystem:
    """Unified capability gateway for Noor's selected open-source data stack.

    Noor owns orchestration and safety. The upstream projects remain independent
    execution engines; their source trees are intentionally not copied into Noor.
    """

    def __init__(self) -> None:
        self._engines = {engine.name: engine for engine in ENGINES}

    def catalog(self) -> list[dict[str, Any]]:
        return [
            {
                "name": engine.name,
                "repository": engine.repository,
                "purpose": engine.purpose,
                "capabilities": list(engine.capabilities),
                "optional_dependency": engine.optional_dependency,
                "requires_service": engine.requires_service,
                "available": self._available(engine),
            }
            for engine in ENGINES
        ]

    def available(self) -> list[str]:
        return [engine.name for engine in ENGINES if self._available(engine)]

    def select(
        self,
        *,
        task: str,
        source: str | None = None,
        rows: int | None = None,
        sql: bool = False,
        validation: bool = False,
    ) -> str:
        text = task.casefold()
        suffix = Path(source).suffix.casefold() if source else ""

        if validation or any(term in text for term in ("validate", "quality", "expectation", "data quality")):
            if self._available(self._engines["great_expectations"]):
                return "great_expectations"

        if sql or any(term in text for term in ("sql", "query", "join", "cte", "window function")):
            if self._available(self._engines["duckdb"]):
                return "duckdb"

        if rows is not None and rows >= 1_000_000 and self._available(self._engines["polars"]):
            return "polars"

        if suffix in {".parquet", ".csv", ".jsonl", ".ndjson"} and self._available(self._engines["polars"]):
            if any(term in text for term in ("large", "fast", "stream", "performance", "millions")):
                return "polars"

        return "pandas"

    @staticmethod
    def _available(engine: EngineCapability) -> bool:
        if engine.requires_service:
            return False
        if not engine.optional_dependency:
            return True
        try:
            __import__(engine.optional_dependency)
            return True
        except ImportError:
            return False


class DataEcosystemSkill:
    """High-level operations that keep engine selection behind one Noor API."""

    def __init__(self) -> None:
        self.ecosystem = DataEcosystem()

    def capabilities(self) -> dict[str, Any]:
        return {
            "engines": self.ecosystem.catalog(),
            "available_engines": self.ecosystem.available(),
            "principle": "Noor orchestrates; upstream open-source projects execute specialized workloads.",
        }

    def select_engine(self, **kwargs: Any) -> dict[str, Any]:
        selected = self.ecosystem.select(**kwargs)
        engine = self.ecosystem._engines[selected]
        return {
            "engine": selected,
            "repository": engine.repository,
            "purpose": engine.purpose,
            "capabilities": list(engine.capabilities),
        }

    def execute_sql(self, query: str, source: str) -> dict[str, Any]:
        if not query.strip():
            raise ValueError("SQL query cannot be empty")
        forbidden = ("insert", "update", "delete", "drop", "alter", "create", "replace", "truncate")
        normalized = query.strip().casefold()
        if not (normalized.startswith("select") or normalized.startswith("with") or normalized.startswith("describe") or normalized.startswith("show")):
            raise ValueError("Only read-only SQL statements are allowed")
        if any(token in normalized.split() for token in forbidden):
            raise ValueError("Write or schema-mutating SQL is blocked")
        try:
            import duckdb
        except ImportError as exc:
            raise RuntimeError("DuckDB support is not installed; install Noor's data-engine extra") from exc

        suffix = Path(source).suffix.casefold()
        if suffix == ".parquet":
            relation = f"read_parquet('{Path(source).as_posix()}')"
        elif suffix in {".csv", ".tsv"}:
            relation = f"read_csv_auto('{Path(source).as_posix()}')"
        else:
            raise ValueError("DuckDB file SQL currently supports CSV/TSV/Parquet sources")
        rewritten = query.replace("__NOOR_SOURCE__", relation)
        with duckdb.connect() as connection:
            frame = connection.execute(rewritten).fetchdf()
        return {
            "engine": "duckdb",
            "repository": "duckdb/duckdb",
            "rows": int(len(frame)),
            "columns": [str(column) for column in frame.columns],
            "records": frame.where(frame.notna(), None).to_dict(orient="records"),
            "verified": True,
        }
