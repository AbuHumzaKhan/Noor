from __future__ import annotations

from pathlib import Path
from typing import Any


def profile_data(context: dict[str, Any]) -> dict[str, Any]:
    """Create a deterministic profile for a supported tabular dataset."""
    path_value = context.get("path")
    if not path_value:
        raise ValueError("data.profile requires an input 'path'")

    path = Path(str(path_value)).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"Dataset not found: {path}")

    try:
        import pandas as pd
    except ImportError as exc:
        raise RuntimeError("pandas is required for data.profile; install the analytics extra") from exc

    suffix = path.suffix.lower()
    if suffix == ".csv":
        frame = pd.read_csv(path)
    elif suffix == ".tsv":
        frame = pd.read_csv(path, sep="\t")
    elif suffix in {".txt", ".dat", ".data"}:
        frame = pd.read_csv(path, sep=None, engine="python")
    elif suffix in {".json", ".jsonl", ".ndjson"}:
        frame = pd.read_json(path, lines=suffix in {".jsonl", ".ndjson"})
    elif suffix == ".xml":
        frame = pd.read_xml(path)
    elif suffix in {".xlsx", ".xlsm", ".xltx", ".xltm", ".xls", ".ods"}:
        frame = pd.read_excel(path)
    elif suffix == ".parquet":
        frame = pd.read_parquet(path)
    elif suffix == ".feather":
        frame = pd.read_feather(path)
    elif suffix in {".pkl", ".pickle"}:
        frame = pd.read_pickle(path)
    elif suffix == ".sas7bdat":
        frame = pd.read_sas(path, format="sas7bdat")
    elif suffix == ".xpt":
        frame = pd.read_sas(path, format="xport")
    elif suffix in {".sav", ".zsav"}:
        frame = pd.read_spss(path)
    elif suffix == ".dta":
        frame = pd.read_stata(path)
    elif suffix in {".html", ".htm"}:
        tables = pd.read_html(path)
        if not tables:
            raise ValueError("No HTML tables found")
        frame = tables[0]
    elif suffix in {".h5", ".hdf", ".hdf5"}:
        frame = pd.read_hdf(path)
    elif suffix == ".arff":
        try:
            from scipy.io import arff
        except ImportError as exc:
            raise RuntimeError("ARFF profiling requires scipy") from exc
        data, _ = arff.loadarff(path)
        frame = pd.DataFrame(data)
    elif suffix in {".db", ".sqlite", ".sqlite3"}:
        raise ValueError("SQLite profiling requires selecting a table first")
    elif suffix in {".sql", ".avro", ".orc"}:
        raise ValueError(f"{suffix} requires a dedicated table/dataframe load before profiling")
    else:
        raise ValueError(f"Unsupported tabular format: {suffix}")

    columns: list[dict[str, Any]] = []
    for column in frame.columns:
        series = frame[column]
        columns.append({
            "name": str(column),
            "dtype": str(series.dtype),
            "missing_count": int(series.isna().sum()),
            "missing_pct": round(float(series.isna().mean() * 100), 3),
            "unique_count": int(series.nunique(dropna=True)),
            "constant": bool(series.nunique(dropna=False) <= 1),
        })

    return {
        "path": str(path),
        "format": suffix,
        "rows": len(frame),
        "columns": len(frame.columns),
        "duplicate_rows": int(frame.duplicated().sum()),
        "memory_bytes": int(frame.memory_usage(deep=True).sum()),
        "column_profile": columns,
    }
