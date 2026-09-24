from __future__ import annotations

from typing import Any


def verify_result(capability: str, output: dict[str, Any]) -> dict[str, Any]:
    """Perform deterministic structural verification for V1 outputs."""
    if not isinstance(output, dict):
        return {
            "valid": False,
            "capability": capability,
            "errors": ["Provider output must be a dictionary"],
        }

    errors: list[str] = []
    if capability == "excel.inspect":
        if not isinstance(output.get("sheets"), list):
            errors.append("Excel inspection must return a sheets list")
    elif capability == "excel.read":
        if not isinstance(output.get("values"), list):
            errors.append("Excel read must return a values list")
    elif capability == "excel.write":
        if output.get("cells_written", 0) < 1:
            errors.append("Excel write must report at least one written cell")
        if not output.get("output"):
            errors.append("Excel write must report an output path")
    elif capability == "excel.formula.generate":
        if not isinstance(output.get("formula"), str) or not output["formula"].startswith("="):
            errors.append("Formula generation must return an Excel formula")
    elif capability == "excel.transform":
        if not output.get("output"):
            errors.append("Excel transformation must report an output path")
        if not isinstance(output.get("changes"), int):
            errors.append("Excel transformation must report an integer change count")
    elif capability == "excel.analyze":
        if not isinstance(output.get("numeric_summary"), dict):
            errors.append("Excel analysis must return a numeric summary")
        if not isinstance(output.get("rows"), int) or not isinstance(output.get("columns"), int):
            errors.append("Excel analysis must report integer row and column counts")
    elif capability == "data.profile" and not output:
        errors.append("Profile output cannot be empty")

    return {
        "valid": not errors,
        "capability": capability,
        "errors": errors,
    }
