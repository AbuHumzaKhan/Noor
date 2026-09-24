from __future__ import annotations

from pathlib import Path
from typing import Any


def profile_data(context: dict[str, Any]) -> dict[str, Any]:
    """Create a deterministic first-pass profile for a tabular file.

    Input:
        context['path']: CSV, Parquet, or Excel path.

    The task intentionally returns JSON-serializable metadata so later tasks
    can consume the profile without coupling the engine to a UI.
    """

    path_value = context.get("path")
    if not path_value:
        raise ValueError("data.profile requires an input 'path'")

    path = Path(str(path_value)).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"Dataset not found: {path}")

    try:
        import pandas as pd
    except ImportError as exc:
        raise RuntimeError(
            "pandas is required for data.profile; install the analytics extra"
        ) from exc

    suffix = path.suffix.lower()
    if suffix == ".csv":
        frame = pd.read_csv(path)
    elif suffix in {".xlsx", ".xls"}:
        frame = pd.read_excel(path)
    elif suffix == ".parquet":
        frame = pd.read_parquet(path)
    else:
        raise ValueError(f"Unsupported tabular format: {suffix}")

    columns: list[dict[str, Any]] = []
    for column in frame.columns:
        series = frame[column]
        columns.append(
            {
                "name": str(column),
                "dtype": str(series.dtype),
                "missing_count": int(series.isna().sum()),
                "missing_pct": round(float(series.isna().mean() * 100), 3),
                "unique_count": int(series.nunique(dropna=True)),
                "constant": bool(series.nunique(dropna=False) <= 1),
            }
        )

    return {
        "path": str(path),
        "rows": int(len(frame)),
        "columns": int(len(frame.columns)),
        "duplicate_rows": int(frame.duplicated().sum()),
        "memory_bytes": int(frame.memory_usage(deep=True).sum()),
        "column_profile": columns,
    }
