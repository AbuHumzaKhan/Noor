from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any, ClassVar


class ExcelIntelligenceSkill:
    """Deterministic Excel/data-analysis intelligence for Noor.

    This layer answers questions from the actual attached dataset, recommends
    Excel formulas from the detected schema, generates analytical questions,
    creates pivot-style summaries, and produces dashboard/report specifications.
    It does not invent dataset facts: numerical answers are computed from the
    loaded file and include the calculation used.
    """

    SUPPORTED = {
        ".csv", ".tsv", ".txt", ".json", ".jsonl", ".ndjson", ".xml", ".xlsx", ".xlsm",
        ".xltx", ".xltm", ".xls", ".ods", ".parquet", ".feather", ".pkl", ".pickle",
        ".sas7bdat", ".xpt", ".sav", ".zsav", ".dta", ".arff", ".html", ".htm",
    }

    SOURCES: ClassVar[list[dict[str, str]]] = [
        {
            "title": "Microsoft Support — Excel functions by category",
            "url": "https://support.microsoft.com/en-us/excel/excel-functions-by-category",
        },
        {
            "title": "Microsoft Support — Create a PivotTable",
            "url": "https://support.microsoft.com/en-us/excel/get-started/create-a-pivottable-to-analyze-worksheet-data",
        },
        {
            "title": "Microsoft Support — Overview of PivotTables and PivotCharts",
            "url": "https://support.microsoft.com/en-us/excel/overview-of-pivottables-and-pivotcharts",
        },
        {
            "title": "Microsoft Support — Creating charts",
            "url": "https://support.microsoft.com/en-us/excel/creating-charts-from-start-to-finish",
        },
    ]

    FORMULAS: ClassVar[dict[str, dict[str, Any]]] = {
        # Math / aggregation
        "SUM": {"category": "Math", "version": "all", "use": "Add numbers", "template": "=SUM({range})"},
        "SUMIF": {"category": "Math", "version": "all", "use": "Sum values meeting one criterion", "template": "=SUMIF({criteria_range},{criteria},{sum_range})"},
        "SUMIFS": {"category": "Math", "version": "all", "use": "Sum values meeting multiple criteria", "template": "=SUMIFS({sum_range},{criteria_range1},{criteria1},{criteria_range2},{criteria2})"},
        "SUBTOTAL": {"category": "Math", "version": "all", "use": "Aggregate filtered/list data", "template": "=SUBTOTAL(9,{range})"},
        "PRODUCT": {"category": "Math", "version": "all", "use": "Multiply numbers", "template": "=PRODUCT({range})"},
        "ROUND": {"category": "Math", "version": "all", "use": "Round a number", "template": "=ROUND({value},{digits})"},
        "ROUNDUP": {"category": "Math", "version": "all", "use": "Round away from zero", "template": "=ROUNDUP({value},{digits})"},
        "ROUNDDOWN": {"category": "Math", "version": "all", "use": "Round toward zero", "template": "=ROUNDDOWN({value},{digits})"},
        "MROUND": {"category": "Math", "version": "all", "use": "Round to a multiple", "template": "=MROUND({number},{multiple})"},
        "ABS": {"category": "Math", "version": "all", "use": "Absolute value", "template": "=ABS({value})"},
        "MOD": {"category": "Math", "version": "all", "use": "Remainder after division", "template": "=MOD({number},{divisor})"},
        "SUMPRODUCT": {"category": "Math", "version": "all", "use": "Multiply arrays and sum results; useful for weighted calculations", "template": "=SUMPRODUCT({range1},{range2})"},
        "AGGREGATE": {"category": "Math", "version": "2010+", "use": "Aggregate while optionally ignoring errors/hidden rows", "template": "=AGGREGATE({function_num},{options},{array})"},
        # Statistical
        "AVERAGE": {"category": "Statistical", "version": "all", "use": "Arithmetic mean", "template": "=AVERAGE({range})"},
        "AVERAGEIF": {"category": "Statistical", "version": "all", "use": "Average values meeting one criterion", "template": "=AVERAGEIF({criteria_range},{criteria},{average_range})"},
        "AVERAGEIFS": {"category": "Statistical", "version": "all", "use": "Average values meeting multiple criteria", "template": "=AVERAGEIFS({average_range},{criteria_range1},{criteria1})"},
        "COUNT": {"category": "Statistical", "version": "all", "use": "Count numeric cells", "template": "=COUNT({range})"},
        "COUNTA": {"category": "Statistical", "version": "all", "use": "Count non-empty cells", "template": "=COUNTA({range})"},
        "COUNTBLANK": {"category": "Statistical", "version": "all", "use": "Count blank cells", "template": "=COUNTBLANK({range})"},
        "COUNTIF": {"category": "Statistical", "version": "all", "use": "Count cells meeting one criterion", "template": "=COUNTIF({range},{criteria})"},
        "COUNTIFS": {"category": "Statistical", "version": "all", "use": "Count cells meeting multiple criteria", "template": "=COUNTIFS({range1},{criteria1},{range2},{criteria2})"},
        "MAX": {"category": "Statistical", "version": "all", "use": "Largest value", "template": "=MAX({range})"},
        "MIN": {"category": "Statistical", "version": "all", "use": "Smallest value", "template": "=MIN({range})"},
        "MEDIAN": {"category": "Statistical", "version": "all", "use": "Middle value", "template": "=MEDIAN({range})"},
        "MODE.SNGL": {"category": "Statistical", "version": "2010+", "use": "Most frequently occurring numeric value", "template": "=MODE.SNGL({range})"},
        "STDEV.S": {"category": "Statistical", "version": "2010+", "use": "Sample standard deviation", "template": "=STDEV.S({range})"},
        "VAR.S": {"category": "Statistical", "version": "2010+", "use": "Sample variance", "template": "=VAR.S({range})"},
        "RANK.EQ": {"category": "Statistical", "version": "2010+", "use": "Rank a value in a list", "template": "=RANK.EQ({number},{ref},{order})"},
        "PERCENTILE.INC": {"category": "Statistical", "version": "2010+", "use": "Return an inclusive percentile", "template": "=PERCENTILE.INC({array},{k})"},
        "QUARTILE.INC": {"category": "Statistical", "version": "2010+", "use": "Return an inclusive quartile", "template": "=QUARTILE.INC({array},{quart})"},
        # Logical / errors
        "IF": {"category": "Logical", "version": "all", "use": "Return values based on a condition", "template": "=IF({condition},{true_value},{false_value})"},
        "IFS": {"category": "Logical", "version": "2019+", "use": "Evaluate multiple conditions", "template": "=IFS({condition1},{value1},{condition2},{value2})"},
        "AND": {"category": "Logical", "version": "all", "use": "Require all conditions to be true", "template": "=AND({condition1},{condition2})"},
        "OR": {"category": "Logical", "version": "all", "use": "Require at least one condition to be true", "template": "=OR({condition1},{condition2})"},
        "NOT": {"category": "Logical", "version": "all", "use": "Reverse a logical result", "template": "=NOT({logical})"},
        "IFERROR": {"category": "Logical", "version": "2007+", "use": "Return a fallback when a formula errors", "template": "=IFERROR({value},{fallback})"},
        "IFNA": {"category": "Logical", "version": "2013+", "use": "Handle #N/A specifically", "template": "=IFNA({value},{fallback})"},
        "SWITCH": {"category": "Logical", "version": "2016+", "use": "Map an expression to multiple results", "template": "=SWITCH({expression},{case1},{result1},{default})"},
        "LET": {"category": "Logical", "version": "2021+", "use": "Name intermediate calculation results", "template": "=LET({name},{value},{calculation})"},
        # Lookup / dynamic arrays
        "XLOOKUP": {"category": "Lookup", "version": "2021+", "use": "Lookup a value and return a corresponding result", "template": "=XLOOKUP({lookup},{lookup_array},{return_array},{not_found})"},
        "XMATCH": {"category": "Lookup", "version": "2021+", "use": "Return the relative position of a match", "template": "=XMATCH({lookup},{lookup_array})"},
        "VLOOKUP": {"category": "Lookup", "version": "all", "use": "Vertical lookup in the first column of a table", "template": "=VLOOKUP({lookup},{table},{column},FALSE)"},
        "HLOOKUP": {"category": "Lookup", "version": "all", "use": "Horizontal lookup in the first row", "template": "=HLOOKUP({lookup},{table},{row},FALSE)"},
        "INDEX": {"category": "Lookup", "version": "all", "use": "Return a value by row/column position", "template": "=INDEX({array},{row_num},{column_num})"},
        "MATCH": {"category": "Lookup", "version": "all", "use": "Find a relative position", "template": "=MATCH({lookup},{lookup_array},0)"},
        "INDEX+MATCH": {"category": "Lookup", "version": "all", "use": "Two-way compatible lookup pattern", "template": "=INDEX({return_range},MATCH({lookup},{lookup_range},0))"},
        "FILTER": {"category": "Dynamic Array", "version": "2021+", "use": "Return rows matching criteria", "template": "=FILTER({array},{include})"},
        "UNIQUE": {"category": "Dynamic Array", "version": "2021+", "use": "Return distinct values", "template": "=UNIQUE({array})"},
        "SORT": {"category": "Dynamic Array", "version": "2021+", "use": "Sort a range/array", "template": "=SORT({array},{sort_index},{sort_order})"},
        "SORTBY": {"category": "Dynamic Array", "version": "2021+", "use": "Sort an array by another range", "template": "=SORTBY({array},{by_array},{sort_order})"},
        "SEQUENCE": {"category": "Dynamic Array", "version": "2021+", "use": "Generate a sequence of numbers", "template": "=SEQUENCE({rows},{columns},{start},{step})"},
        "TRANSPOSE": {"category": "Dynamic Array", "version": "all", "use": "Switch rows and columns", "template": "=TRANSPOSE({array})"},
        # Text
        "LEFT": {"category": "Text", "version": "all", "use": "Extract characters from the left", "template": "=LEFT({text},{num_chars})"},
        "RIGHT": {"category": "Text", "version": "all", "use": "Extract characters from the right", "template": "=RIGHT({text},{num_chars})"},
        "MID": {"category": "Text", "version": "all", "use": "Extract text from the middle", "template": "=MID({text},{start},{num_chars})"},
        "LEN": {"category": "Text", "version": "all", "use": "Count characters", "template": "=LEN({text})"},
        "TRIM": {"category": "Text", "version": "all", "use": "Remove extra spaces", "template": "=TRIM({text})"},
        "CLEAN": {"category": "Text", "version": "all", "use": "Remove non-printing characters", "template": "=CLEAN({text})"},
        "UPPER": {"category": "Text", "version": "all", "use": "Convert text to uppercase", "template": "=UPPER({text})"},
        "LOWER": {"category": "Text", "version": "all", "use": "Convert text to lowercase", "template": "=LOWER({text})"},
        "PROPER": {"category": "Text", "version": "all", "use": "Capitalize words", "template": "=PROPER({text})"},
        "SUBSTITUTE": {"category": "Text", "version": "all", "use": "Replace text occurrences", "template": "=SUBSTITUTE({text},{old},{new})"},
        "REPLACE": {"category": "Text", "version": "all", "use": "Replace text by position", "template": "=REPLACE({old_text},{start},{num_chars},{new_text})"},
        "TEXT": {"category": "Text", "version": "all", "use": "Format a value as text", "template": "=TEXT({value},{format_text})"},
        "TEXTJOIN": {"category": "Text", "version": "2019+", "use": "Join text with a delimiter", "template": "=TEXTJOIN({delimiter},TRUE,{text1},{text2})"},
        "CONCAT": {"category": "Text", "version": "2019+", "use": "Combine text values", "template": "=CONCAT({text1},{text2})"},
        "TEXTBEFORE": {"category": "Text", "version": "2024+", "use": "Return text before a delimiter", "template": "=TEXTBEFORE({text},{delimiter})"},
        "TEXTAFTER": {"category": "Text", "version": "2024+", "use": "Return text after a delimiter", "template": "=TEXTAFTER({text},{delimiter})"},
        "TEXTSPLIT": {"category": "Text", "version": "2024+", "use": "Split text into rows/columns", "template": "=TEXTSPLIT({text},{col_delimiter},{row_delimiter})"},
        # Date / time
        "TODAY": {"category": "Date & Time", "version": "all", "use": "Current date", "template": "=TODAY()"},
        "NOW": {"category": "Date & Time", "version": "all", "use": "Current date and time", "template": "=NOW()"},
        "YEAR": {"category": "Date & Time", "version": "all", "use": "Extract year", "template": "=YEAR({date})"},
        "MONTH": {"category": "Date & Time", "version": "all", "use": "Extract month number", "template": "=MONTH({date})"},
        "DAY": {"category": "Date & Time", "version": "all", "use": "Extract day number", "template": "=DAY({date})"},
        "EOMONTH": {"category": "Date & Time", "version": "all", "use": "Return month-end date", "template": "=EOMONTH({start_date},{months})"},
        "EDATE": {"category": "Date & Time", "version": "all", "use": "Shift a date by months", "template": "=EDATE({start_date},{months})"},
        "DATEDIF": {"category": "Date & Time", "version": "all", "use": "Calculate elapsed time between dates", "template": "=DATEDIF({start_date},{end_date},{unit})"},
        "NETWORKDAYS": {"category": "Date & Time", "version": "all", "use": "Count working days", "template": "=NETWORKDAYS({start_date},{end_date},{holidays})"},
        "WORKDAY": {"category": "Date & Time", "version": "all", "use": "Return a workday offset", "template": "=WORKDAY({start_date},{days},{holidays})"},
        # Information
        "ISBLANK": {"category": "Information", "version": "all", "use": "Test whether a cell is blank", "template": "=ISBLANK({value})"},
        "ISNUMBER": {"category": "Information", "version": "all", "use": "Test whether a value is numeric", "template": "=ISNUMBER({value})"},
        "ISTEXT": {"category": "Information", "version": "all", "use": "Test whether a value is text", "template": "=ISTEXT({value})"},
        "ISERROR": {"category": "Information", "version": "all", "use": "Test whether a value is an error", "template": "=ISERROR({value})"},
        "N": {"category": "Information", "version": "all", "use": "Convert a value to a number where possible", "template": "=N({value})"},
    }

    def _load(self, path: str, sheet_name: str | None = None):
        try:
            import pandas as pd
        except ImportError as exc:
            raise RuntimeError("Excel intelligence requires pandas") from exc
        source = Path(path).expanduser()
        if source.suffix.lower() not in self.SUPPORTED:
            raise ValueError(f"Unsupported analysis format: {source.suffix}")
        if not source.is_file():
            raise FileNotFoundError(source)
        suffix = source.suffix.lower()
        kwargs: dict[str, Any] = {}
        if sheet_name:
            kwargs["sheet_name"] = sheet_name
        if suffix == ".csv": frame = pd.read_csv(source)
        elif suffix == ".tsv": frame = pd.read_csv(source, sep="\t")
        elif suffix in {".txt", ".dat", ".data"}: frame = pd.read_csv(source, sep=None, engine="python")
        elif suffix in {".jsonl", ".ndjson"}: frame = pd.read_json(source, lines=True)
        elif suffix == ".json": frame = pd.read_json(source)
        elif suffix == ".xml": frame = pd.read_xml(source)
        elif suffix in {".xlsx", ".xlsm", ".xltx", ".xltm", ".xls", ".ods"}: frame = pd.read_excel(source, **kwargs)
        elif suffix == ".parquet": frame = pd.read_parquet(source)
        elif suffix == ".feather": frame = pd.read_feather(source)
        elif suffix in {".pkl", ".pickle"}: frame = pd.read_pickle(source)
        elif suffix in {".sas7bdat", ".xpt"}: frame = pd.read_sas(source, format="xport" if suffix == ".xpt" else "sas7bdat")
        elif suffix in {".sav", ".zsav"}: frame = pd.read_spss(source)
        elif suffix == ".dta": frame = pd.read_stata(source)
        elif suffix in {".html", ".htm"}:
            tables = pd.read_html(source)
            if not tables: raise ValueError("No HTML table found")
            frame = tables[0]
        elif suffix == ".arff":
            from scipy.io import arff
            data, _ = arff.loadarff(source)
            frame = pd.DataFrame(data)
        else: raise ValueError(f"Unsupported analysis format: {suffix}")
        frame.columns = [str(column) for column in frame.columns]
        return frame

    @staticmethod
    def _normalise(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", " ", str(value).casefold()).strip()

    def _find_column(self, frame, text: str, *, numeric: bool | None = None, date: bool = False) -> str | None:
        query = self._normalise(text)
        scored: list[tuple[int, str]] = []
        for column in frame.columns:
            name = self._normalise(column)
            score = 0
            if name == query: score += 100
            if query and query in name: score += 50
            q_tokens = set(query.split())
            n_tokens = set(name.split())
            score += len(q_tokens & n_tokens) * 12
            if numeric is True and not self._is_numeric(frame[column]): score -= 100
            if numeric is False and self._is_numeric(frame[column]): score -= 20
            if date and not self._is_date_like(frame[column]): score -= 100
            if score > 0: scored.append((score, column))
        return max(scored, default=(0, None))[1]

    @staticmethod
    def _is_numeric(series) -> bool:
        try:
            import pandas as pd
            return bool(pd.api.types.is_numeric_dtype(series))
        except Exception:
            return False

    @staticmethod
    def _is_date_like(series) -> bool:
        try:
            import pandas as pd
            if pd.api.types.is_datetime64_any_dtype(series): return True
            sample = series.dropna().head(30)
            if sample.empty: return False
            parsed = pd.to_datetime(sample, errors="coerce")
            return float(parsed.notna().mean()) >= 0.8
        except Exception:
            return False

    @staticmethod
    def _excel_col(index: int) -> str:
        result = ""
        number = index + 1
        while number:
            number, rem = divmod(number - 1, 26)
            result = chr(65 + rem) + result
        return result

    def profile(self, path: str, sheet_name: str | None = None) -> dict[str, Any]:
        import pandas as pd
        frame = self._load(path, sheet_name)
        numeric = frame.select_dtypes(include="number")
        missing = int(frame.isna().sum().sum())
        profile_columns: list[dict[str, Any]] = []
        for column in frame.columns:
            series = frame[column]
            item: dict[str, Any] = {
                "name": column,
                "dtype": str(series.dtype),
                "missing": int(series.isna().sum()),
                "missing_pct": round(float(series.isna().mean() * 100), 2),
                "unique": int(series.nunique(dropna=True)),
                "constant": bool(series.nunique(dropna=False) <= 1),
                "example_values": [self._safe_value(v) for v in series.dropna().head(5).tolist()],
            }
            if self._is_numeric(series):
                clean = pd.to_numeric(series, errors="coerce").dropna()
                item.update({
                    "min": self._safe_value(clean.min()) if not clean.empty else None,
                    "max": self._safe_value(clean.max()) if not clean.empty else None,
                    "mean": self._safe_value(clean.mean()) if not clean.empty else None,
                    "median": self._safe_value(clean.median()) if not clean.empty else None,
                    "std": self._safe_value(clean.std()) if len(clean) > 1 else None,
                })
            elif self._is_date_like(series):
                parsed = pd.to_datetime(series, errors="coerce")
                item.update({"date_min": self._safe_value(parsed.min()), "date_max": self._safe_value(parsed.max())})
            else:
                top = series.dropna().astype(str).value_counts().head(5)
                item["top_values"] = [{"value": str(k), "count": int(v)} for k, v in top.items()]
            profile_columns.append(item)
        return {
            "path": str(Path(path).resolve()), "sheet": sheet_name, "rows": int(len(frame)),
            "columns": int(len(frame.columns)), "missing_cells": missing,
            "duplicate_rows": int(frame.duplicated().sum()),
            "numeric_columns": [str(c) for c in numeric.columns],
            "date_columns": [str(c) for c in frame.columns if self._is_date_like(frame[c])],
            "column_profile": profile_columns,
            "sources": self.SOURCES,
        }

    def answer_question(self, path: str, question: str, sheet_name: str | None = None) -> dict[str, Any]:
        import pandas as pd
        frame = self._load(path, sheet_name)
        text = question.casefold().strip()
        if not text: raise ValueError("Question cannot be empty")

        if any(term in text for term in ("missing value", "missing values", "blank", "blanks", "null")):
            missing = frame.isna().sum().sort_values(ascending=False)
            rows = [{"column": str(k), "missing": int(v), "percentage": round(float(v / max(len(frame), 1) * 100), 2)} for k, v in missing.items() if v]
            return self._answer(question, f"I found {int(frame.isna().sum().sum()):,} missing cells across {len(rows)} columns.", rows, "frame.isna().sum()")

        if "duplicate" in text:
            count = int(frame.duplicated().sum())
            return self._answer(question, f"The dataset contains {count:,} duplicate rows.", {"duplicate_rows": count, "percentage": round(count / max(len(frame), 1) * 100, 2)}, "frame.duplicated().sum()")

        if any(term in text for term in ("correlation", "correlate", "relationship between")):
            numeric = frame.select_dtypes(include="number")
            corr = numeric.corr(numeric_only=True)
            pairs: list[dict[str, Any]] = []
            for i, left in enumerate(corr.columns):
                for right in corr.columns[i + 1:]:
                    value = corr.loc[left, right]
                    if pd.notna(value): pairs.append({"column_1": left, "column_2": right, "correlation": round(float(value), 4)})
            pairs.sort(key=lambda x: abs(x["correlation"]), reverse=True)
            return self._answer(question, f"I calculated {len(pairs):,} numeric column pairs.", pairs[:10], "numeric_dataframe.corr()")

        if any(term in text for term in ("top ", "highest", "largest", "best")):
            number_match = re.search(r"top\s+(\d+)", text)
            limit = int(number_match.group(1)) if number_match else 5
            column_hint = re.sub(r"\b(top\s+\d+|highest|largest|best)\b", "", text).strip()
            column = self._find_column(frame, column_hint, numeric=True) if column_hint else None
            column = column or (str(frame.select_dtypes(include="number").columns[0]) if len(frame.select_dtypes(include="number").columns) else None)
            if not column: raise ValueError("I could not identify a numeric column for the ranking.")
            result = frame[[column]].copy().sort_values(column, ascending=False).head(limit)
            return self._answer(question, f"The highest {limit} values in {column} are shown below.", result.to_dict(orient="records"), f"{column}.sort_values(ascending=False).head({limit})")

        numeric_columns = list(frame.select_dtypes(include="number").columns)
        requested = self._find_column(frame, text, numeric=True)
        if requested is None:
            for candidate in numeric_columns:
                if self._normalise(candidate) in self._normalise(text): requested = candidate; break
        if requested is None and numeric_columns: requested = numeric_columns[0]

        if requested is not None:
            series = pd.to_numeric(frame[requested], errors="coerce").dropna()
            if any(term in text for term in ("average", "mean", "avg")):
                value = float(series.mean()) if not series.empty else None
                return self._answer(question, f"The average of {requested} is {self._format_number(value)}.", {"column": requested, "average": value, "count": int(series.size)}, f"AVERAGE({requested})")
            if any(term in text for term in ("median", "middle")):
                value = float(series.median()) if not series.empty else None
                return self._answer(question, f"The median of {requested} is {self._format_number(value)}.", {"column": requested, "median": value}, f"MEDIAN({requested})")
            if any(term in text for term in ("maximum", "max", "highest")):
                value = float(series.max()) if not series.empty else None
                return self._answer(question, f"The maximum of {requested} is {self._format_number(value)}.", {"column": requested, "maximum": value}, f"MAX({requested})")
            if any(term in text for term in ("minimum", "min", "lowest")):
                value = float(series.min()) if not series.empty else None
                return self._answer(question, f"The minimum of {requested} is {self._format_number(value)}.", {"column": requested, "minimum": value}, f"MIN({requested})")
            if any(term in text for term in ("count", "how many", "number of")) and not any(term in text for term in ("sum", "total")):
                value = int(series.size)
                return self._answer(question, f"There are {value:,} non-empty numeric values in {requested}.", {"column": requested, "count": value}, f"COUNT({requested})")
            if any(term in text for term in ("sum", "total", "sales", "revenue", "amount")):
                value = float(series.sum()) if not series.empty else 0.0
                return self._answer(question, f"The total of {requested} is {self._format_number(value)}.", {"column": requested, "sum": value, "count": int(series.size)}, f"SUM({requested})")

        if "how many" in text or "count" in text:
            value = len(frame)
            return self._answer(question, f"The dataset contains {value:,} rows.", {"rows": value}, "ROWS(data)")

        raise ValueError("I could not map the question to a deterministic calculation. Ask about totals, averages, counts, minimum/maximum, missing values, duplicates, rankings, or correlations, or ask which Excel formula to use.")

    def recommend_formula(self, path: str, request: str, sheet_name: str | None = None, excel_version: str = "2021") -> dict[str, Any]:
        frame = self._load(path, sheet_name)
        text = request.casefold()
        numeric = list(frame.select_dtypes(include="number").columns)
        categorical = [str(c) for c in frame.columns if c not in numeric]
        column = self._find_column(frame, request, numeric=True) if numeric else None
        column = column or (numeric[0] if numeric else None)
        idx = list(frame.columns).index(column) if column in frame.columns else 0
        ref = f"{self._excel_col(idx)}2:{self._excel_col(idx)}{len(frame) + 1}" if column else "A2:A100"

        if any(term in text for term in ("lookup", "look up", "match", "find corresponding")):
            preferred = "XLOOKUP" if excel_version not in {"2016", "2019"} else "INDEX+MATCH"
            reason = "XLOOKUP is the modern lookup choice; for Excel 2019 use INDEX+MATCH because XLOOKUP is not available there."
            formula = "=XLOOKUP(A2,LookupTable[ID],LookupTable[Result],\"Not found\")" if preferred == "XLOOKUP" else "=INDEX(ReturnRange,MATCH(A2,LookupRange,0))"
        elif any(term in text for term in ("multiple criteria", "multiple conditions", "several criteria")) and any(term in text for term in ("sum", "total")):
            preferred, formula, reason = "SUMIFS", "=SUMIFS(SumRange,CriteriaRange1,Criteria1,CriteriaRange2,Criteria2)", "Use SUMIFS when the total must satisfy more than one condition."
        elif any(term in text for term in ("criteria", "condition", "where")) and any(term in text for term in ("sum", "total")):
            preferred, formula, reason = "SUMIF", "=SUMIF(CriteriaRange,Criteria,SumRange)", "Use SUMIF when a total depends on one criterion."
        elif any(term in text for term in ("average", "mean")):
            preferred, formula, reason = "AVERAGE", f"=AVERAGE({ref})", "Use AVERAGE for the arithmetic mean of numeric values."
        elif any(term in text for term in ("count", "how many")):
            preferred, formula, reason = "COUNT", f"=COUNT({ref})", "Use COUNT for numeric cells; use COUNTA when text/non-empty cells should also count."
        elif any(term in text for term in ("missing", "blank")):
            preferred, formula, reason = "COUNTBLANK", f"=COUNTBLANK({ref})", "Use COUNTBLANK to count empty cells in a range."
        elif any(term in text for term in ("duplicate", "duplicates")):
            preferred, formula, reason = "COUNTIF", f"=COUNTIF({ref},{self._excel_col(idx)}2)>1", "COUNTIF can flag values that occur more than once; use COUNTIFS for multi-column duplicate keys."
        elif any(term in text for term in ("error", "errors")):
            preferred, formula, reason = "IFERROR", f"=IFERROR({self._excel_col(idx)}2,\"Check\")", "IFERROR returns a controlled fallback when a calculation evaluates to an Excel error."
        elif any(term in text for term in ("percentage", "%", "margin", "rate", "growth")):
            preferred, formula, reason = "IFERROR", "=IFERROR(Numerator/Denominator,0)", "Use IFERROR around ratios so a zero/invalid denominator does not produce an uncontrolled error."
        elif any(term in text for term in ("clean", "spaces", "text cleanup")):
            preferred, formula, reason = "TRIM + CLEAN", f"=TRIM(CLEAN({self._excel_col(idx)}2))", "TRIM removes extra spaces and CLEAN removes non-printing characters."
        elif any(term in text for term in ("unique", "distinct")):
            preferred, formula, reason = "UNIQUE", f"=UNIQUE({ref})", "UNIQUE returns distinct values; it requires Excel 2021 or newer."
        elif any(term in text for term in ("filter", "filtered list")):
            preferred, formula, reason = "FILTER", f"=FILTER(A2:Z{len(frame)+1},{self._excel_col(idx)}2:{self._excel_col(idx)}{len(frame)+1}=\"criteria\")", "FILTER returns rows matching criteria and requires a dynamic-array version of Excel."
        elif any(term in text for term in ("rank", "ranking", "top")):
            preferred, formula, reason = "RANK.EQ", f"=RANK.EQ({self._excel_col(idx)}2,{ref},0)", "RANK.EQ assigns a rank within a numeric range."
        elif any(term in text for term in ("date", "year", "month")):
            preferred, formula, reason = "YEAR/MONTH", f"=YEAR({self._excel_col(idx)}2)", "YEAR/MONTH/DAY are appropriate for extracting date components."
        else:
            preferred, formula, reason = "SUM", f"=SUM({ref})", "For a numeric total, SUM is the direct aggregation formula."

        return {
            "request": request, "recommended_function": preferred, "formula": formula,
            "reason": reason, "detected_column": column, "excel_version": excel_version,
            "compatible": self._compatibility(preferred, excel_version), "sources": self.SOURCES,
        }

    def generate_questions(self, path: str, sheet_name: str | None = None, limit: int = 12) -> dict[str, Any]:
        frame = self._load(path, sheet_name)
        numeric = [str(c) for c in frame.select_dtypes(include="number").columns]
        categorical = [str(c) for c in frame.columns if c not in numeric]
        dates = [str(c) for c in frame.columns if self._is_date_like(frame[c])]
        questions: list[str] = []
        for column in numeric[:4]:
            questions.extend([f"What is the total of {column}?", f"What is the average of {column}?", f"What are the minimum and maximum values of {column}?"])
        for column in categorical[:3]:
            questions.append(f"What are the most common values in {column}?")
            if numeric:
                questions.append(f"What is the total {numeric[0]} by {column}?")
        if dates and numeric:
            questions.append(f"How does {numeric[0]} change over time using {dates[0]}?")
        questions.extend(["How many missing values are in the dataset?", "Are there duplicate rows?", "Which numeric columns are most strongly correlated?"])
        unique: list[str] = []
        for question in questions:
            if question not in unique: unique.append(question)
        return {"questions": unique[:max(1, limit)], "basis": {"numeric_columns": numeric, "categorical_columns": categorical, "date_columns": dates}}

    def pivot_summary(self, path: str, row_field: str, value_field: str | None = None, column_field: str | None = None, aggfunc: str = "sum", sheet_name: str | None = None) -> dict[str, Any]:
        frame = self._load(path, sheet_name)
        if row_field not in frame.columns: raise ValueError(f"Unknown row field: {row_field}")
        if value_field and value_field not in frame.columns: raise ValueError(f"Unknown value field: {value_field}")
        if column_field and column_field not in frame.columns: raise ValueError(f"Unknown column field: {column_field}")
        allowed = {"sum", "mean", "count", "min", "max", "median"}
        if aggfunc not in allowed: raise ValueError(f"Unsupported aggregation: {aggfunc}")
        values = value_field or frame.select_dtypes(include="number").columns[0] if len(frame.select_dtypes(include="number").columns) else None
        if not values: raise ValueError("A numeric value field is required for this pivot summary")
        table = frame.pivot_table(index=row_field, columns=column_field, values=values, aggfunc=aggfunc, fill_value=0) if column_field else frame.groupby(row_field, dropna=False)[values].agg(aggfunc).reset_index()
        if column_field:
            table = table.reset_index()
            table.columns = [" | ".join(str(v) for v in col if str(v) != "") if isinstance(col, tuple) else str(col) for col in table.columns]
        return {"row_field": row_field, "value_field": values, "column_field": column_field, "aggregation": aggfunc, "rows": table.to_dict(orient="records"), "row_count": len(table), "source_rows": len(frame)}

    def dashboard_spec(self, path: str, sheet_name: str | None = None) -> dict[str, Any]:
        frame = self._load(path, sheet_name)
        numeric = [str(c) for c in frame.select_dtypes(include="number").columns]
        categorical = [str(c) for c in frame.columns if c not in numeric]
        dates = [str(c) for c in frame.columns if self._is_date_like(frame[c])]
        kpis = [{"name": f"Total {c}", "formula": f"=SUM({self._excel_col(list(frame.columns).index(c))}2:{self._excel_col(list(frame.columns).index(c))}{len(frame)+1})"} for c in numeric[:4]]
        charts: list[dict[str, Any]] = []
        if dates and numeric: charts.append({"type": "line", "x": dates[0], "y": numeric[0], "purpose": "trend over time"})
        if categorical and numeric: charts.append({"type": "bar", "x": categorical[0], "y": numeric[0], "purpose": "category comparison"})
        if len(numeric) >= 2: charts.append({"type": "scatter", "x": numeric[0], "y": numeric[1], "purpose": "numeric relationship"})
        return {"dataset_rows": len(frame), "dataset_columns": len(frame.columns), "kpis": kpis, "charts": charts, "recommended_features": ["Excel Table", "Pivot-style summaries", "Slicers/filters", "Conditional formatting", "KPI cards", "Data-quality indicators"], "sources": self.SOURCES}

    def formula_catalog(self, category: str | None = None, query: str | None = None) -> dict[str, Any]:
        items = []
        for name, item in self.FORMULAS.items():
            if category and item["category"].casefold() != category.casefold(): continue
            if query and query.casefold() not in (name + " " + item["use"]).casefold(): continue
            items.append({"name": name, **item})
        return {"count": len(items), "formulas": items, "sources": [self.SOURCES[0]]}

    @staticmethod
    def _compatibility(function: str, version: str) -> bool:
        if version in {"2021", "2024", "365"}: return True
        if version == "2019": return function not in {"XLOOKUP", "XMATCH", "FILTER", "UNIQUE", "SORT", "SORTBY", "SEQUENCE", "LET", "TEXTBEFORE", "TEXTAFTER", "TEXTSPLIT"}
        if version == "2016": return function not in {"XLOOKUP", "XMATCH", "FILTER", "UNIQUE", "SORT", "SORTBY", "SEQUENCE", "LET", "IFS", "SWITCH", "TEXTBEFORE", "TEXTAFTER", "TEXTSPLIT"}
        return True

    @staticmethod
    def _safe_value(value: Any) -> Any:
        if value is None: return None
        if hasattr(value, "isoformat"): return value.isoformat()
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)): return None
        if hasattr(value, "item"):
            try: return value.item()
            except Exception: pass
        return value

    @staticmethod
    def _format_number(value: Any) -> str:
        if value is None: return "not available"
        if isinstance(value, float): return f"{value:,.2f}"
        return f"{value:,}"

    @staticmethod
    def _answer(question: str, summary: str, evidence: Any, calculation: str) -> dict[str, Any]:
        return {"question": question, "answer": summary, "evidence": evidence, "calculation": calculation, "verified": True, "basis": "computed directly from the attached dataset"}
