from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path
from typing import Any, ClassVar


class DataIngestSkill:
    """Inspect and load common structured/tabular data formats safely."""

    SUPPORTED_EXTENSIONS: ClassVar[dict[str, str]] = {
        ".csv": "CSV", ".tsv": "TSV", ".txt": "Delimited text", ".json": "JSON",
        ".jsonl": "JSON Lines", ".ndjson": "NDJSON", ".xml": "XML", ".xlsx": "Excel",
        ".xlsm": "Excel macro-enabled", ".xltx": "Excel template", ".xltm": "Excel macro template",
        ".xls": "Legacy Excel", ".ods": "OpenDocument spreadsheet", ".parquet": "Parquet",
        ".feather": "Feather", ".pkl": "Pickle", ".pickle": "Pickle", ".sas7bdat": "SAS",
        ".xpt": "SAS transport", ".sav": "SPSS", ".zsav": "SPSS compressed", ".dta": "Stata",
        ".arff": "ARFF", ".h5": "HDF5", ".hdf": "HDF5", ".hdf5": "HDF5",
        ".html": "HTML tables", ".htm": "HTML tables", ".sql": "SQL script", ".db": "SQLite",
        ".sqlite": "SQLite", ".sqlite3": "SQLite", ".avro": "Avro", ".orc": "ORC",
        ".dat": "Delimited/fixed-width text", ".data": "Delimited text",
    }

    def validate_path(self, path: str) -> Path:
        file_path = Path(path).expanduser()
        if file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported dataset format: {file_path.suffix or 'unknown'}")
        if not file_path.exists():
            raise FileNotFoundError(file_path)
        if not file_path.is_file():
            raise ValueError(f"Dataset path is not a file: {file_path}")
        return file_path

    def inspect(self, path: str) -> dict[str, Any]:
        file_path = self.validate_path(path)
        suffix = file_path.suffix.lower()
        result: dict[str, Any] = {
            "path": str(file_path),
            "format": self.SUPPORTED_EXTENSIONS[suffix],
            "extension": suffix,
            "bytes": file_path.stat().st_size,
        }
        if suffix in {".json", ".jsonl", ".ndjson", ".xml"}:
            result["preview"] = self._text_preview(file_path)
        elif suffix in {".db", ".sqlite", ".sqlite3"}:
            result["tables"] = self._sqlite_tables(file_path)
        return result

    def load(self, path: str, *, sheet_name: str | None = None, nrows: int = 1000) -> dict[str, Any]:
        if nrows < 1 or nrows > 100_000:
            raise ValueError("nrows must be between 1 and 100000")
        file_path = self.validate_path(path)
        suffix = file_path.suffix.lower()
        try:
            import pandas as pd
        except ImportError as exc:
            raise RuntimeError("Data ingestion requires pandas") from exc

        if suffix in {".jsonl", ".ndjson"}:
            frame = pd.read_json(file_path, lines=True, nrows=nrows)
        elif suffix == ".json":
            frame = pd.read_json(file_path, nrows=nrows)
        elif suffix == ".xml":
            frame = pd.read_xml(file_path)
            frame = frame.head(nrows)
        elif suffix == ".csv":
            frame = pd.read_csv(file_path, nrows=nrows)
        elif suffix == ".tsv":
            frame = pd.read_csv(file_path, sep="\t", nrows=nrows)
        elif suffix in {".txt", ".dat", ".data"}:
            frame = pd.read_csv(file_path, sep=None, engine="python", nrows=nrows)
        elif suffix in {".xlsx", ".xlsm", ".xltx", ".xltm", ".xls", ".ods"}:
            frame = pd.read_excel(file_path, sheet_name=sheet_name or 0, nrows=nrows)
        elif suffix == ".parquet":
            frame = pd.read_parquet(file_path).head(nrows)
        elif suffix == ".feather":
            frame = pd.read_feather(file_path).head(nrows)
        elif suffix in {".pkl", ".pickle"}:
            frame = pd.read_pickle(file_path).head(nrows)
        elif suffix == ".sas7bdat":
            frame = pd.read_sas(file_path, format="sas7bdat").head(nrows)
        elif suffix == ".xpt":
            frame = pd.read_sas(file_path, format="xport").head(nrows)
        elif suffix in {".sav", ".zsav"}:
            frame = pd.read_spss(file_path).head(nrows)
        elif suffix == ".dta":
            frame = pd.read_stata(file_path).head(nrows)
        elif suffix == ".arff":
            frame = self._read_arff(file_path).head(nrows)
        elif suffix in {".html", ".htm"}:
            tables = pd.read_html(file_path)
            if not tables:
                raise ValueError("No HTML tables found")
            frame = tables[0].head(nrows)
        elif suffix in {".h5", ".hdf", ".hdf5"}:
            frame = pd.read_hdf(file_path).head(nrows)
        elif suffix in {".db", ".sqlite", ".sqlite3"}:
            table = sheet_name or self._sqlite_tables(file_path)[0]
            if not table:
                raise ValueError("SQLite database contains no tables")
            self._validate_sql_identifier(table)
            frame = pd.read_sql_query(f'SELECT * FROM "{table}" LIMIT {nrows}', sqlite3.connect(file_path))
        elif suffix in {".sql"}:
            raise ValueError("SQL scripts are inspected only in V1; provide a database file for loading")
        elif suffix in {".avro", ".orc"}:
            reader = pd.read_avro if suffix == ".avro" else pd.read_orc
            frame = reader(file_path).head(nrows)
        else:
            raise ValueError(f"No loader registered for {suffix}")

        return {
            "path": str(file_path),
            "format": self.SUPPORTED_EXTENSIONS[suffix],
            "rows_returned": len(frame),
            "columns": [str(column) for column in frame.columns],
            "dtypes": {str(column): str(dtype) for column, dtype in frame.dtypes.items()},
            "records": frame.where(frame.notna(), None).to_dict(orient="records"),
        }

    @staticmethod
    def _text_preview(path: Path, limit: int = 2000) -> str:
        return path.read_text(encoding="utf-8", errors="replace")[:limit]

    @staticmethod
    def _sqlite_tables(path: Path) -> list[str]:
        with sqlite3.connect(path) as connection:
            rows = connection.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
        return [str(row[0]) for row in rows]

    @staticmethod
    def _validate_sql_identifier(identifier: str) -> None:
        if not identifier.replace("_", "").isalnum():
            raise ValueError("Invalid SQLite table name")

    @staticmethod
    def _read_arff(path: Path):
        try:
            from scipy.io import arff
        except ImportError as exc:
            raise RuntimeError("ARFF support requires scipy") from exc
        import pandas as pd
        data, _ = arff.loadarff(path)
        return pd.DataFrame(data)
