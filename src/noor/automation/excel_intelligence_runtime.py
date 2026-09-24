from __future__ import annotations

from os import PathLike
from pathlib import Path
from typing import Any

from .excel_intelligence import ExcelIntelligenceSkill


class RuntimeExcelIntelligenceSkill(ExcelIntelligenceSkill):
    """Runtime-safe Excel intelligence wrapper.

    The web/orchestra boundary may carry a dataset reference as a plain path or
    as a small upload metadata object. Normalize that reference before pandas
    or pathlib sees it, and handle capability-discovery questions without
    pretending they are numerical questions.
    """

    @staticmethod
    def _dataset_path(value: Any) -> str:
        if isinstance(value, (str, PathLike)):
            path = str(value).strip()
            if path:
                return path

        if isinstance(value, dict):
            for key in ("path", "file_path", "filepath", "source_path"):
                if key in value:
                    return RuntimeExcelIntelligenceSkill._dataset_path(value[key])
            upload = value.get("upload")
            if upload is not None:
                return RuntimeExcelIntelligenceSkill._dataset_path(upload)

        raise TypeError(
            "Dataset reference must be a file path or upload metadata containing a path."
        )

    def _load(self, path: Any, sheet_name: str | None = None):
        normalized_path = self._dataset_path(path)
        normalized_sheet = None if sheet_name is None else str(sheet_name)
        return super()._load(normalized_path, normalized_sheet)

    def profile(self, path: Any, sheet_name: str | None = None) -> dict[str, Any]:
        return super().profile(self._dataset_path(path), None if sheet_name is None else str(sheet_name))

    def answer_question(self, path: Any, question: str, sheet_name: str | None = None) -> dict[str, Any]:
        normalized_path = self._dataset_path(path)
        normalized_sheet = None if sheet_name is None else str(sheet_name)
        text = str(question).casefold().strip()

        capability_terms = (
            "what can i do",
            "what can i do with",
            "what can you do",
            "what can noor do",
            "what can i analyze",
            "what can i analyse",
            "what can i ask",
            "what are the capabilities",
            "what can be done",
        )
        if any(term in text for term in capability_terms):
            frame = self._load(normalized_path, normalized_sheet)
            numeric = [str(column) for column in frame.select_dtypes(include="number").columns]
            categorical = [str(column) for column in frame.columns if column not in numeric]
            dates = [str(column) for column in frame.columns if self._is_date_like(frame[column])]
            missing = int(frame.isna().sum().sum())
            duplicates = int(frame.duplicated().sum())
            capabilities = [
                "Inspect the dataset structure and schema",
                "Profile columns, data types, missing values, duplicates, and distributions",
                "Ask natural-language questions and get answers computed from the dataset",
                "Generate useful analytical questions automatically",
                "Recommend Excel formulas based on the dataset and your request",
                "Create pivot-style summaries and grouped analysis",
                "Recommend KPIs, charts, and dashboard/report layouts",
                "Investigate correlations and numeric relationships",
                "Identify data-quality issues that need cleaning",
                "Search and work with supported Excel workbooks",
                "Create native Excel PivotTables/charts when desktop Excel automation is available",
            ]
            summary = (
                f"You can use Noor as a data-analysis and Excel workspace for this dataset. "
                f"It contains {len(frame):,} rows and {len(frame.columns):,} columns, including "
                f"{len(numeric)} numeric, {len(categorical)} non-numeric, and {len(dates)} date-like columns. "
                f"There are {missing:,} missing cells and {duplicates:,} duplicate rows."
            )
            examples = [
                "Analyze the complete data",
                "Profile the dataset and show data-quality issues",
                "What is the total of <numeric column>?",
                "Which columns have missing values?",
                "What are the top 10 values by <numeric column>?",
                "Which numeric columns are most strongly correlated?",
                "What Excel formula should I use for a lookup?",
                "Create a pivot summary of <numeric column> by <category column>",
                "Design a dashboard for this dataset",
            ]
            return {
                "question": question,
                "answer": summary,
                "capabilities": capabilities,
                "suggested_commands": examples,
                "dataset_context": {
                    "rows": int(len(frame)),
                    "columns": int(len(frame.columns)),
                    "numeric_columns": numeric,
                    "categorical_columns": categorical,
                    "date_columns": dates,
                    "missing_cells": missing,
                    "duplicate_rows": duplicates,
                },
                "verified": True,
                "basis": "computed directly from the attached dataset and Noor's registered Excel capabilities",
                "sources": self.SOURCES,
            }

        return super().answer_question(normalized_path, question, normalized_sheet)
