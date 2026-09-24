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
    if capability == "excel.inspect" and not isinstance(output.get("sheets"), list):
        errors.append("Excel inspection must return a sheets list")
    elif capability == "data.profile" and not output:
        errors.append("Profile output cannot be empty")

    return {
        "valid": not errors,
        "capability": capability,
        "errors": errors,
    }
