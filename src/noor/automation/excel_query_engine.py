from __future__ import annotations

import re
from typing import Any

from .excel_intelligence import ExcelIntelligenceSkill


class ExcelQueryEngine:
    """Schema-aware natural-language query engine for arbitrary tabular data."""

    AGGREGATIONS = {
        "sum": ("sum", "total", "totals", "sales", "revenue", "amount", "cost", "value"),
        "mean": ("average", "avg", "mean"),
        "median": ("median",),
        "min": ("minimum", "lowest", "smallest"),
        "max": ("maximum", "highest", "largest"),
        "count": ("count", "counts", "how many", "number of", "no of"),
    }

    def __init__(self) -> None:
        self.skill = ExcelIntelligenceSkill()

    @staticmethod
    def _normalise(text: str) -> str:
        return re.sub(r"[^a-z0-9]+", " ", str(text).casefold()).strip()

    @staticmethod
    def _tokens(text: str) -> set[str]:
        return set(ExcelQueryEngine._normalise(text).split())

    def _resolve_column(self, frame, phrase: str, *, numeric: bool | None = None) -> tuple[str | None, float]:
        query = self._normalise(phrase)
        if not query:
            return None, 0.0
        q_tokens = self._tokens(phrase)
        aliases = {
            "cost": {"cost", "price", "amount", "expense", "spend", "value"},
            "sales": {"sales", "sale", "revenue", "turnover", "amount"},
            "service": {"service", "servicing", "maintenance"},
            "city": {"city", "location", "town", "place"},
            "brand": {"brand", "make", "manufacturer"},
            "customer": {"customer", "client", "buyer", "owner"},
            "date": {"date", "day", "month", "year", "time"},
        }
        candidates: list[tuple[float, str]] = []
        for column in frame.columns:
            name = self._normalise(column)
            n_tokens = self._tokens(column)
            score = 0.0
            if name == query:
                score += 100
            if query in name or name in query:
                score += 55
            score += len(q_tokens & n_tokens) * 20
            for token in q_tokens:
                if token in aliases and n_tokens & aliases[token]:
                    score += 15
            if numeric is True and not self.skill._is_numeric(frame[column]):
                score -= 100
            if numeric is False and self.skill._is_numeric(frame[column]):
                score -= 20
            if score > 0:
                candidates.append((score, str(column)))
        if not candidates:
            return None, 0.0
        candidates.sort(reverse=True)
        score, column = candidates[0]
        return column, min(score / 100.0, 1.0)

    def _extract_group_phrase(self, text: str) -> str | None:
        patterns = (
            r"(?:by|per|group\s+by|grouped\s+by|for\s+each|each)\s+([a-z0-9_ -]+?)\s*(?:\?|$)",
            r"([a-z0-9_ -]+?)\s+wise\b",
        )
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip(" .,;:")
                value = re.sub(r"\b(?:total|sum|average|avg|mean|count|number|of)\b", " ", value, flags=re.I).strip()
                if value:
                    return value
        return None

    def _extract_filter(self, text: str, frame) -> tuple[str | None, str | None]:
        match = re.search(r"\bwhere\s+([a-z0-9_ -]+?)\s+(?:is|=|equals)\s+['\"]?([^'\"?,]+)", text, re.I)
        if match:
            column, _ = self._resolve_column(frame, match.group(1), numeric=False)
            return (column, match.group(2).strip()) if column else (None, None)

        match = re.search(r"\b(?:in|for)\s+([A-Z][A-Za-z ._-]+?)\s*(?:\?|$)", text)
        if match:
            value = match.group(1).strip()
            for column in frame.columns:
                if not self.skill._is_numeric(frame[column]):
                    values = frame[column].dropna().astype(str)
                    if values.str.casefold().eq(value.casefold()).any():
                        return str(column), value
        return None, None

    def _extract_value_phrase(self, text: str, group_phrase: str | None) -> str:
        cleaned = text
        if group_phrase:
            cleaned = re.sub(re.escape(group_phrase), " ", cleaned, flags=re.I)
        cleaned = re.sub(
            r"\b(?:what|tell me|show me|calculate|find|give me|please|the|total|sum|average|avg|mean|median|minimum|maximum|highest|lowest|count|number of|how many|by|per|wise|each|grouped|group|of|for|in|where|is|are|does|do|can|i|you|me|data|dataset|this|there)\b",
            " ", cleaned, flags=re.I,
        )
        cleaned = re.sub(r"\b(?:top|first|last)\s+\d+\b", " ", cleaned, flags=re.I)
        return re.sub(r"\s+", " ", cleaned).strip(" ?.,")

    def _aggregation(self, text: str) -> str:
        lowered = text.casefold()
        for operation, terms in self.AGGREGATIONS.items():
            if any(re.search(rf"\b{re.escape(term)}\b", lowered) for term in terms):
                return operation
        return "sum"

    @staticmethod
    def _limit(text: str) -> int | None:
        match = re.search(r"\btop\s+(\d+)\b", text.casefold())
        return int(match.group(1)) if match else None

    def answer(self, path: str, question: str, sheet_name: str | None = None) -> dict[str, Any]:
        import pandas as pd

        frame = self.skill._load(path, sheet_name)
        text = question.strip()
        lowered = text.casefold()
        if not text:
            raise ValueError("Question cannot be empty")

        if any(term in lowered for term in ("what can i do", "what i can do", "what can i do with", "what can i analyse", "what can i analyze", "what can noor do", "what can you do", "what i can ask", "what can i ask", "capabilities")):
            numeric = [str(c) for c in frame.select_dtypes(include="number").columns]
            categorical = [str(c) for c in frame.columns if c not in numeric]
            dates = [str(c) for c in frame.columns if self.skill._is_date_like(frame[c])]
            capabilities = [
                "profile the dataset and inspect data quality",
                "calculate totals, averages, medians, minimums, maximums and counts",
                "compare metrics by category, city, brand or any other column",
                "find top/bottom performers and rankings",
                "analyse trends when a date/time field exists",
                "check missing values, duplicates and correlations",
                "recommend Excel formulas, PivotTables, reports and dashboards",
            ]
            return {
                "question": question,
                "answer": "I can analyse this dataset using its detected schema and return computed evidence.",
                "evidence": {"capabilities": capabilities, "numeric_columns": numeric, "categorical_columns": categorical, "date_columns": dates},
                "calculation": "schema-driven capability discovery",
                "resolved_query": {"intent": "capability_discovery"},
                "verified": True,
                "basis": "derived from the attached dataset schema and enabled analytical capabilities",
            }

        if any(term in lowered for term in ("correlation", "correlate", "missing", "blank", "duplicate")):
            return self.skill.answer_question(path, question, sheet_name)

        group_phrase = self._extract_group_phrase(text)
        group_column, group_confidence = self._resolve_column(frame, group_phrase or "") if group_phrase else (None, 0.0)
        aggregation = self._aggregation(lowered)
        limit = self._limit(text)
        filter_column, filter_value = self._extract_filter(text, frame)
        numeric_columns = list(frame.select_dtypes(include="number").columns)
        value_phrase = self._extract_value_phrase(text, group_phrase)
        value_column, value_confidence = self._resolve_column(frame, value_phrase, numeric=True)

        if group_column:
            working_frame = frame
            if filter_column and filter_value:
                working_frame = frame.loc[frame[filter_column].astype(str).str.casefold().eq(filter_value.casefold())].copy()

            if aggregation == "count" and value_column is None:
                grouped = working_frame.groupby(group_column, dropna=False).size().rename("count").reset_index()
                metric_column = "count"
            else:
                value_column = value_column or (str(numeric_columns[0]) if numeric_columns else None)
                if value_column is None:
                    raise ValueError("I identified the grouping field but could not identify a numeric value field.")
                working = working_frame.assign(__noor_value=pd.to_numeric(working_frame[value_column], errors="coerce"))
                if aggregation == "sum":
                    grouped = working.groupby(group_column, dropna=False)["__noor_value"].sum(min_count=1).reset_index(name=value_column)
                elif aggregation == "mean":
                    grouped = working.groupby(group_column, dropna=False)["__noor_value"].mean().reset_index(name=value_column)
                elif aggregation == "median":
                    grouped = working.groupby(group_column, dropna=False)["__noor_value"].median().reset_index(name=value_column)
                elif aggregation == "min":
                    grouped = working.groupby(group_column, dropna=False)["__noor_value"].min().reset_index(name=value_column)
                elif aggregation == "max":
                    grouped = working.groupby(group_column, dropna=False)["__noor_value"].max().reset_index(name=value_column)
                else:
                    grouped = working.groupby(group_column, dropna=False)["__noor_value"].count().reset_index(name=value_column)
                metric_column = value_column

            if limit:
                grouped = grouped.sort_values(metric_column, ascending=False).head(limit)
            else:
                grouped = grouped.sort_values(metric_column, ascending=False, na_position="last")

            records = [{str(k): self.skill._safe_value(v) for k, v in row.items()} for row in grouped.to_dict(orient="records")]
            action = {"sum": "total", "mean": "average", "median": "median", "min": "minimum", "max": "maximum", "count": "count"}[aggregation]
            summary = f"{action.capitalize()} {metric_column} by {group_column}."
            if filter_column and filter_value:
                summary += f" Filter: {filter_column} = {filter_value}."
            return {
                "question": question,
                "answer": summary,
                "evidence": records,
                "calculation": {"operation": aggregation, "group_by": group_column, "value": metric_column, "filter": {"column": filter_column, "value": filter_value} if filter_column else None, "source_rows": int(len(frame)), "rows_after_filter": int(len(working_frame)), "result_rows": int(len(records))},
                "resolved_query": {"intent": "group_aggregate", "group_column": group_column, "value_column": metric_column, "aggregation": aggregation, "group_confidence": round(group_confidence, 3), "value_confidence": round(value_confidence, 3)},
                "verified": True,
                "basis": "computed directly from the attached dataset",
            }

        if filter_column and filter_value:
            mask = frame[filter_column].astype(str).str.casefold().eq(filter_value.casefold())
            filtered = frame.loc[mask]
        else:
            filtered = frame

        value_column = value_column or (str(numeric_columns[0]) if numeric_columns else None)
        if value_column is not None:
            series = pd.to_numeric(filtered[value_column], errors="coerce").dropna()
            if aggregation == "sum": value = float(series.sum())
            elif aggregation == "mean": value = float(series.mean()) if not series.empty else None
            elif aggregation == "median": value = float(series.median()) if not series.empty else None
            elif aggregation == "min": value = float(series.min()) if not series.empty else None
            elif aggregation == "max": value = float(series.max()) if not series.empty else None
            else: value = int(series.size)
            return {
                "question": question,
                "answer": f"{aggregation.capitalize()} of {value_column} = {self.skill._format_number(value)}.",
                "evidence": {"column": value_column, "value": value, "rows_considered": int(len(filtered))},
                "calculation": f"{aggregation.upper()}({value_column})",
                "resolved_query": {"intent": "scalar_aggregate", "value_column": value_column, "aggregation": aggregation, "filter_column": filter_column, "filter_value": filter_value, "value_confidence": round(value_confidence, 3)},
                "verified": True,
                "basis": "computed directly from the attached dataset",
            }

        return self.skill.answer_question(path, question, sheet_name)
