from __future__ import annotations

from typing import Any

from .excel_intelligence import ExcelIntelligenceSkill


class FullExcelAnalysisSkill:
    """Run a bounded, evidence-first analysis package over the attached data."""

    def __init__(self) -> None:
        self.intelligence = ExcelIntelligenceSkill()

    def run(self, path: str, sheet_name: str | None = None) -> dict[str, Any]:
        profile = self.intelligence.profile(path, sheet_name)
        questions = self.intelligence.generate_questions(path, sheet_name, limit=12)
        dashboard = self.intelligence.dashboard_spec(path, sheet_name)

        numeric = profile.get("numeric_columns", [])
        formula_guidance: list[dict[str, Any]] = []
        for column in numeric[:8]:
            formula_guidance.append(
                self.intelligence.recommend_formula(path, f"total {column}", sheet_name, "2021")
            )

        findings: list[dict[str, Any]] = []
        missing_columns = [c for c in profile.get("column_profile", []) if c.get("missing", 0) > 0]
        constant_columns = [c for c in profile.get("column_profile", []) if c.get("constant")]
        if missing_columns:
            findings.append({"type": "data_quality", "severity": "review", "message": f"{len(missing_columns)} column(s) contain missing values."})
        else:
            findings.append({"type": "data_quality", "severity": "clear", "message": "No missing values were detected."})
        if profile.get("duplicate_rows", 0):
            findings.append({"type": "data_quality", "severity": "review", "message": f"{profile['duplicate_rows']:,} duplicate row(s) were detected."})
        else:
            findings.append({"type": "data_quality", "severity": "clear", "message": "No duplicate rows were detected."})
        if constant_columns:
            findings.append({"type": "schema", "severity": "review", "message": f"{len(constant_columns)} column(s) contain only one distinct value."})
        if numeric:
            findings.append({"type": "analysis", "severity": "info", "message": f"Detected {len(numeric)} numeric column(s) suitable for aggregation and KPI analysis."})
        if profile.get("date_columns") and numeric:
            findings.append({"type": "analysis", "severity": "info", "message": "Date and numeric fields support trend analysis."})

        return {
            "profile": profile,
            "questions": questions["questions"],
            "dashboard": dashboard,
            "formula_guidance": formula_guidance,
            "findings": findings,
            "verified_basis": "All dataset metrics are computed from the attached file; Excel guidance is based on the formula/function knowledge catalog.",
        }
