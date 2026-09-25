from __future__ import annotations

from dataclasses import dataclass, field
from difflib import SequenceMatcher
import re
from typing import Any


@dataclass(frozen=True)
class ColumnInfo:
    name: str
    normalized: str
    kind: str
    unique_count: int
    non_null_count: int
    samples: tuple[str, ...] = ()


@dataclass(frozen=True)
class FilterSpec:
    column: str
    operator: str
    value: Any


@dataclass
class QueryPlan:
    """Structured execution plan produced from a natural-language data query."""

    intent: str
    dimensions: list[str] = field(default_factory=list)
    measure: str | None = None
    aggregation: str = "sum"
    filters: list[FilterSpec] = field(default_factory=list)
    limit: int | None = None
    sort_by: str | None = None
    sort_direction: str = "desc"
    confidence: float = 0.0
    assumptions: list[str] = field(default_factory=list)
    alternatives: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent,
            "dimensions": list(self.dimensions),
            "measure": self.measure,
            "aggregation": self.aggregation,
            "filters": [
                {"column": f.column, "operator": f.operator, "value": f.value}
                for f in self.filters
            ],
            "limit": self.limit,
            "sort": {"by": self.sort_by, "direction": self.sort_direction},
            "confidence": round(self.confidence, 3),
            "assumptions": list(self.assumptions),
            "alternatives": list(self.alternatives),
        }


class SchemaResolver:
    """Resolve natural-language field references against an actual DataFrame schema."""

    ALIASES = {
        "city": {"city", "location", "town", "place"},
        "brand": {"brand", "make", "manufacturer"},
        "model": {"model", "product", "item"},
        "customer": {"customer", "client", "buyer", "owner"},
        "cost": {"cost", "expense", "spend", "amount", "value", "price"},
        "sales": {"sales", "sale", "revenue", "turnover"},
        "service": {"service", "servicing", "maintenance"},
        "date": {"date", "day", "time", "period"},
        "year": {"year", "yr"},
        "quantity": {"quantity", "qty", "units", "count"},
        "type": {"type", "kind", "category"},
    }

    STOPWORDS = {
        "a", "an", "the", "me", "my", "this", "that", "data", "dataset",
        "please", "tell", "show", "give", "calculate", "find", "what", "is",
        "are", "was", "were", "do", "does", "can", "you", "i", "we", "of",
        "for", "to", "from", "with", "using", "and", "or", "in", "on", "by",
        "per", "wise", "each", "group", "grouped", "total", "sum", "average",
        "avg", "mean", "median", "minimum", "maximum", "highest", "lowest",
        "largest", "smallest", "top", "bottom", "number", "how", "many", "compare",
        "comparison", "percentage", "percent", "share", "contribution", "trend",
        "over", "time", "distribution", "relationship", "correlation", "rank", "ranked",
    }

    def inspect(self, frame) -> list[ColumnInfo]:
        columns: list[ColumnInfo] = []
        for column in frame.columns:
            series = frame[column]
            if self._is_numeric(series):
                kind = "numeric"
            elif self._is_date_like(series):
                kind = "date"
            else:
                kind = "categorical"
            samples = tuple(str(v) for v in series.dropna().head(5).tolist())
            columns.append(
                ColumnInfo(
                    name=str(column),
                    normalized=self.normalize(str(column)),
                    kind=kind,
                    unique_count=int(series.nunique(dropna=True)),
                    non_null_count=int(series.notna().sum()),
                    samples=samples,
                )
            )
        return columns

    def resolve(
        self,
        phrase: str,
        frame,
        *,
        preferred_kind: str | None = None,
        exclude: set[str] | None = None,
    ) -> tuple[str | None, float, list[dict[str, Any]]]:
        query = self.normalize(phrase)
        if not query:
            return None, 0.0, []
        q_tokens = set(query.split()) - self.STOPWORDS
        excluded = exclude or set()
        candidates: list[tuple[float, str, ColumnInfo]] = []
        for info in self.inspect(frame):
            if info.name in excluded:
                continue
            score = self._score(query, q_tokens, info)
            if preferred_kind and info.kind == preferred_kind:
                score += 18
            elif preferred_kind and info.kind != preferred_kind:
                score -= 12
            if score > 0:
                candidates.append((score, info.name, info))
        candidates.sort(key=lambda item: (-item[0], item[1].casefold()))
        if not candidates:
            return None, 0.0, []
        best_score, best_name, _ = candidates[0]
        confidence = min(best_score / 100.0, 1.0)
        alternatives = [
            {"column": name, "confidence": round(min(score / 100.0, 1.0), 3), "kind": info.kind}
            for score, name, info in candidates[:4]
        ]
        return best_name, confidence, alternatives

    def resolve_value(self, phrase: str, frame) -> tuple[str | None, Any]:
        value = phrase.strip(" \t\"'.,;:?")
        if not value:
            return None, None
        # Prefer an exact categorical value match before guessing a field.
        for info in self.inspect(frame):
            if info.kind == "numeric":
                continue
            series = frame[info.name].dropna().astype(str)
            matches = series[series.str.casefold() == value.casefold()]
            if not matches.empty:
                return info.name, matches.iloc[0]
        return None, None

    @classmethod
    def normalize(cls, text: str) -> str:
        text = re.sub(r"[_/\\-]+", " ", str(text).casefold())
        return re.sub(r"[^a-z0-9.]+", " ", text).strip()

    @classmethod
    def _score(cls, query: str, q_tokens: set[str], info: ColumnInfo) -> float:
        name_tokens = set(info.normalized.split())
        score = 0.0
        if query == info.normalized:
            score += 100
        elif query in info.normalized or info.normalized in query:
            score += 62
        score += 18 * len(q_tokens & name_tokens)
        compact_query = query.replace(" ", "")
        compact_name = info.normalized.replace(" ", "")
        if compact_query and compact_name:
            score += 28 * SequenceMatcher(None, compact_query, compact_name).ratio()
        for token in q_tokens:
            for alias_key, aliases in cls.ALIASES.items():
                if token == alias_key or token in aliases:
                    if name_tokens & aliases or alias_key in name_tokens:
                        score += 12
        return score

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
            if pd.api.types.is_datetime64_any_dtype(series):
                return True
            if pd.api.types.is_numeric_dtype(series):
                return False
            sample = series.dropna().astype(str).head(100)
            if sample.empty:
                return False
            parsed = pd.to_datetime(sample, errors="coerce")
            return bool(parsed.notna().mean() >= 0.8)
        except Exception:
            return False


class ExcelQueryPlanner:
    """Turn natural-language analytical requests into deterministic query plans."""

    AGGREGATION_TERMS = {
        "mean": ("average", "avg", "mean"),
        "median": ("median",),
        "min": ("minimum", "lowest", "smallest"),
        "max": ("maximum", "highest", "largest"),
        "count": ("count", "how many", "number of", "no of", "records"),
        "sum": ("sum", "total", "sales", "revenue", "amount", "cost", "value"),
    }

    def __init__(self) -> None:
        self.schema = SchemaResolver()

    def plan(self, question: str, frame) -> QueryPlan:
        text = question.strip()
        lowered = text.casefold()
        if not text:
            raise ValueError("Question cannot be empty")

        if self._is_capability_request(lowered):
            return QueryPlan("capability_discovery", confidence=0.99)

        if self._is_quality_request(lowered):
            return QueryPlan("data_quality", confidence=0.95)

        aggregation = self._aggregation(lowered)
        limit = self._limit(lowered)
        group_phrase = self._group_phrase(lowered)
        dimensions: list[str] = []
        alternatives: list[dict[str, Any]] = []
        assumptions: list[str] = []

        if group_phrase:
            group_column, group_confidence, alternatives = self.schema.resolve(
                group_phrase, frame, preferred_kind="categorical"
            )
            if not group_column:
                group_column, group_confidence, alternatives = self.schema.resolve(group_phrase, frame)
            if group_column:
                dimensions.append(group_column)
        else:
            group_column = None
            group_confidence = 0.0

        measure_phrase = self._measure_phrase(lowered, group_phrase)
        measure = None
        measure_confidence = 0.0
        if measure_phrase:
            measure, measure_confidence, measure_alternatives = self.schema.resolve(
                measure_phrase, frame, preferred_kind="numeric"
            )
            alternatives = alternatives or measure_alternatives

        filter_specs = self._filters(lowered, frame)

        if not measure and aggregation == "count":
            # Count queries can operate on rows without a numeric measure.
            measure_confidence = 1.0
        elif not measure:
            numeric = [str(c) for c in frame.select_dtypes(include="number").columns]
            if len(numeric) == 1:
                measure = numeric[0]
                measure_confidence = 0.62
                assumptions.append(f"Only one numeric column was available, so '{measure}' was selected as the measure.")
            elif len(numeric) == 0:
                raise ValueError("I could not identify a numeric measure for this calculation.")
            else:
                raise ValueError(
                    "I understood the analytical request but could not identify the measure. "
                    "Name the numeric field, for example: 'service cost by city'."
                )

        if not dimensions and self._is_rank_request(lowered):
            raise ValueError("I need a grouping field for the ranking, for example: 'top 5 cities by service cost'.")

        intent = "scalar_aggregate"
        sort_by = measure
        sort_direction = "desc"

        if self._is_contribution_request(lowered) and dimensions:
            intent = "percentage_contribution"
        elif self._is_trend_request(lowered):
            intent = "trend"
            if not dimensions:
                date_column, date_confidence, date_alternatives = self._resolve_date_dimension(frame)
                if date_column:
                    dimensions = [date_column]
                    group_confidence = date_confidence
                    alternatives = alternatives or date_alternatives
                else:
                    raise ValueError("I could not find a date/time column for a trend analysis.")
        elif self._is_distribution_request(lowered):
            intent = "distribution"
            dimensions = []
        elif self._is_correlation_request(lowered):
            intent = "correlation"
            dimensions = []
            measure = None
        elif dimensions:
            intent = "rank" if self._is_rank_request(lowered) else "group_aggregate"
        elif self._is_comparison_request(lowered):
            intent = "comparison"
        
        if "lowest" in lowered or "smallest" in lowered or "bottom" in lowered:
            sort_direction = "asc"
        if intent == "rank" and limit is None:
            limit = 1

        confidence = self._plan_confidence(
            intent, group_confidence, measure_confidence, bool(filter_specs), bool(dimensions)
        )
        if confidence < 0.55:
            raise ValueError(
                "I could not confidently map the question to the dataset schema. "
                "Please mention the field you want to calculate and, if applicable, the field to group by."
            )

        return QueryPlan(
            intent=intent,
            dimensions=dimensions,
            measure=measure,
            aggregation=aggregation,
            filters=filter_specs,
            limit=limit,
            sort_by=sort_by,
            sort_direction=sort_direction,
            confidence=confidence,
            assumptions=assumptions,
            alternatives=alternatives[:4],
        )

    def _group_phrase(self, text: str) -> str | None:
        patterns = (
            r"\b(?:by|per|grouped\s+by|group\s+by|for\s+each|each)\s+([a-z0-9_ .-]+?)(?=\s+(?:with|using|where|for|in|over|and)\b|\?|$)",
            r"\b([a-z0-9_ .-]+?)\s+wise\b",
        )
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                phrase = re.sub(r"\b(?:total|sum|average|avg|mean|median|count|number|of)\b", " ", match.group(1)).strip()
                if phrase:
                    return phrase
        return None

    def _measure_phrase(self, text: str, group_phrase: str | None) -> str | None:
        cleaned = text
        if group_phrase:
            cleaned = re.sub(re.escape(group_phrase), " ", cleaned)
        cleaned = re.sub(r"\btop\s+\d+\b", " ", cleaned)
        cleaned = re.sub(
            r"\b(?:what|tell|show|calculate|find|give|please|the|total|sum|average|avg|mean|median|minimum|maximum|highest|lowest|largest|smallest|count|number|of|by|per|wise|each|group|grouped|for|in|where|is|are|does|do|can|i|you|me|data|dataset|this|there|compare|comparison|percentage|percent|share|contribution|trend|over|time|distribution|relationship|correlation|rank|ranked)\b",
            " ",
            cleaned,
        )
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" ?.,")
        return cleaned or None

    def _filters(self, text: str, frame) -> list[FilterSpec]:
        filters: list[FilterSpec] = []
        # Explicit conditions: where City is Lucknow / City = Lucknow.
        for match in re.finditer(
            r"\bwhere\s+([a-z0-9_ .-]+?)\s+(?:is|=|equals)\s+['\"]?([^'\"?,]+)",
            text,
        ):
            column, _, _ = self.schema.resolve(match.group(1), frame)
            if column:
                filters.append(FilterSpec(column, "eq", match.group(2).strip()))

        # Natural categorical constraints: "in Lucknow", "for Honda", "in Mumbai".
        for match in re.finditer(r"\b(?:in|for)\s+([a-z][a-z0-9 ._-]+?)(?=\s+(?:and|with|where|by|per)\b|\?|$)", text):
            value = match.group(1).strip()
            column, resolved_value = self.schema.resolve_value(value, frame)
            if column and not any(f.column == column and str(f.value).casefold() == str(resolved_value).casefold() for f in filters):
                filters.append(FilterSpec(column, "eq", resolved_value))
        return filters

    def _resolve_date_dimension(self, frame) -> tuple[str | None, float, list[dict[str, Any]]]:
        candidates = []
        for info in self.schema.inspect(frame):
            if info.kind == "date":
                score = 70.0
                if "date" in info.normalized or "time" in info.normalized or "year" in info.normalized:
                    score += 20
                candidates.append((score, info.name, info))
        candidates.sort(reverse=True)
        if not candidates:
            return None, 0.0, []
        score, name, info = candidates[0]
        return name, min(score / 100, 1.0), [{"column": name, "confidence": min(score / 100, 1.0), "kind": info.kind}]

    @staticmethod
    def _aggregation(text: str) -> str:
        for operation, terms in ExcelQueryPlanner.AGGREGATION_TERMS.items():
            if any(re.search(rf"\b{re.escape(term)}\b", text) for term in terms):
                return operation
        return "sum"

    @staticmethod
    def _limit(text: str) -> int | None:
        match = re.search(r"\b(?:top|bottom|first|last)\s+(\d+)\b", text)
        return int(match.group(1)) if match else None

    @staticmethod
    def _is_capability_request(text: str) -> bool:
        return any(term in text for term in (
            "what can i do", "what can i do with", "what can i analyze", "what can i analyse",
            "what can noor do", "what can you do", "what can i ask", "capabilities",
        ))

    @staticmethod
    def _is_quality_request(text: str) -> bool:
        return any(term in text for term in (
            "missing values", "missing data", "blank values", "duplicates", "duplicate rows",
            "data quality", "quality check", "data validation",
        ))

    @staticmethod
    def _is_rank_request(text: str) -> bool:
        return any(term in text for term in ("top ", "bottom ", "highest", "lowest", "largest", "smallest", "rank"))

    @staticmethod
    def _is_comparison_request(text: str) -> bool:
        return any(term in text for term in ("compare", "comparison", "versus", " vs ", "difference between"))

    @staticmethod
    def _is_contribution_request(text: str) -> bool:
        return any(term in text for term in ("percentage", "percent", "share", "contribution", "% of total"))

    @staticmethod
    def _is_trend_request(text: str) -> bool:
        return any(term in text for term in ("trend", "over time", "by month", "by year", "monthly", "yearly", "growth"))

    @staticmethod
    def _is_distribution_request(text: str) -> bool:
        return any(term in text for term in ("distribution", "spread", "quartile", "percentile", "variance", "standard deviation"))

    @staticmethod
    def _is_correlation_request(text: str) -> bool:
        return any(term in text for term in ("correlation", "correlate", "relationship between"))

    @staticmethod
    def _plan_confidence(intent: str, group_confidence: float, measure_confidence: float, has_filter: bool, has_dimension: bool) -> float:
        if intent in {"capability_discovery", "data_quality", "correlation", "distribution"}:
            return 0.95
        score = 0.25
        score += min(group_confidence, 1.0) * (0.3 if has_dimension else 0.0)
        score += min(measure_confidence, 1.0) * 0.4
        score += 0.1 if has_filter else 0.0
        score += 0.1 if intent in {"group_aggregate", "rank", "percentage_contribution", "trend"} and has_dimension else 0.0
        return min(score, 0.99)
