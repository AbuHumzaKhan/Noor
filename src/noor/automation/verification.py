from __future__ import annotations

from typing import Any


def verify_result(capability: str, output: dict[str, Any]) -> dict[str, Any]:
    """Perform deterministic structural verification for V1 outputs."""
    if not isinstance(output, dict):
        return {"valid": False, "capability": capability, "errors": ["Provider output must be a dictionary"]}

    errors: list[str] = []
    if capability == "excel.inspect":
        if not isinstance(output.get("sheets"), list): errors.append("Excel inspection must return a sheets list")
    elif capability == "excel.read":
        if not isinstance(output.get("values"), list): errors.append("Excel read must return a values list")
    elif capability == "excel.write":
        if output.get("cells_written", 0) < 1: errors.append("Excel write must report at least one written cell")
        if not output.get("output"): errors.append("Excel write must report an output path")
    elif capability == "excel.formula.generate":
        if not isinstance(output.get("formula"), str) or not output["formula"].startswith("="): errors.append("Formula generation must return an Excel formula")
    elif capability == "excel.transform":
        if not output.get("output"): errors.append("Excel transformation must report an output path")
        if not isinstance(output.get("changes"), int): errors.append("Excel transformation must report an integer change count")
    elif capability == "excel.analyze":
        if not isinstance(output.get("numeric_summary"), dict): errors.append("Excel analysis must return a numeric summary")
        if not isinstance(output.get("rows"), int) or not isinstance(output.get("columns"), int): errors.append("Excel analysis must report integer row and column counts")
    elif capability == "excel.intelligence.profile":
        if not isinstance(output.get("column_profile"), list): errors.append("Deep profile must return column_profile")
        if not isinstance(output.get("rows"), int) or not isinstance(output.get("columns"), int): errors.append("Deep profile must report integer row and column counts")
    elif capability == "excel.intelligence.answer":
        if not output.get("answer"): errors.append("Dataset answer must contain an answer")
        if output.get("verified") is not True: errors.append("Dataset answer must be marked verified")
    elif capability == "excel.intelligence.formula":
        if not output.get("formula") or not output.get("recommended_function"): errors.append("Formula recommendation must contain a function and formula")
    elif capability == "excel.intelligence.questions":
        if not isinstance(output.get("questions"), list) or not output["questions"]: errors.append("Question generation must return questions")
    elif capability == "excel.intelligence.pivot":
        if not isinstance(output.get("rows"), list): errors.append("Pivot summary must return rows")
    elif capability == "excel.intelligence.dashboard":
        if not isinstance(output.get("kpis"), list) or not isinstance(output.get("charts"), list): errors.append("Dashboard specification must return KPIs and charts")
    elif capability == "excel.intelligence.formulas":
        if not isinstance(output.get("formulas"), list): errors.append("Formula catalog must return formulas")
    elif capability == "excel.intelligence.full_analysis":
        if not isinstance(output.get("profile"), dict): errors.append("Full analysis must include a profile")
        if not isinstance(output.get("questions"), list): errors.append("Full analysis must include generated questions")
        if not isinstance(output.get("findings"), list): errors.append("Full analysis must include findings")
        if not isinstance(output.get("dashboard"), dict): errors.append("Full analysis must include a dashboard specification")
    elif capability == "excel.native.pivot":
        if output.get("native") is not True: errors.append("Native PivotTable execution must report native=true")
        if not output.get("output"): errors.append("Native PivotTable must report an output workbook")
    elif capability == "excel.native.chart":
        if output.get("native") is not True: errors.append("Native chart execution must report native=true")
        if not output.get("output"): errors.append("Native chart must report an output workbook")
    elif capability == "data.profile" and not output:
        errors.append("Profile output cannot be empty")

    return {"valid": not errors, "capability": capability, "errors": errors}
