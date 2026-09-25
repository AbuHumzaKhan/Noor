# NOOR Data Ecosystem

NOOR uses selected open-source projects as specialized execution engines. NOOR does **not** copy their repositories into the project. This keeps licensing, upgrades, security boundaries, and maintenance manageable while giving NOOR one orchestration layer.

## Integrated projects

| Engine | Upstream repository | NOOR role |
|---|---|---|
| pandas | `pandas-dev/pandas` | Default dataframe analysis, cleaning, Excel/CSV/database I/O |
| DuckDB | `duckdb/duckdb` | Read-only analytical SQL over CSV/Parquet and dataframe workflows |
| Polars | `pola-rs/polars` | High-performance, lazy, streaming and larger-data workloads |
| Great Expectations | `great-expectations/great_expectations` | Data-quality expectations and validation |
| Apache Superset | `apache/superset` | Optional BI/visualization service layer |

## Routing policy

NOOR selects an engine from task semantics and dataset characteristics:

1. Data-quality/validation tasks -> Great Expectations when installed.
2. SQL/query/join/window-function tasks -> DuckDB when installed.
3. Very large or performance-oriented dataframe tasks -> Polars when installed.
4. General tabular analysis -> pandas.
5. Superset is treated as an external service rather than an in-process Python dependency.

## Installation

The base package remains lightweight. Install the optional ecosystem engines with:

```powershell
python -m pip install -e ".[analytics,data-engines]"
```

## SQL safety

NOOR exposes DuckDB through a read-only analytical boundary. The current file-query adapter accepts CSV/TSV/Parquet sources and uses `__NOOR_SOURCE__` as the source relation placeholder.

Example:

```sql
SELECT category, SUM(sales) AS total_sales
FROM __NOOR_SOURCE__
GROUP BY category
ORDER BY total_sales DESC;
```

Write and schema-mutating statements are rejected by the NOOR boundary.

## Architecture

```text
User request
    |
    v
NOOR planner / orchestra
    |
    v
DataEcosystemSkill
    |
    +--> pandas -------- general analysis
    +--> DuckDB -------- SQL analytics
    +--> Polars -------- high-performance analytics
    +--> Great Expectations -- validation
    +--> Superset ------ optional BI service
    |
    v
verification / evidence
    |
    v
NOOR response
```

The adapters are deliberately thin. Upstream projects remain responsible for their own execution semantics; NOOR is responsible for intent, routing, permissions, verification, and user-facing behavior.
