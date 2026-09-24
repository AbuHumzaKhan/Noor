from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar


class ExcelSkill:
    """Safe Excel capability boundary for Noor V1.

    The skill focuses on deterministic workbook inspection first. Mutating
    operations should be added behind explicit capabilities and verification.
    """

    SUPPORTED_EXTENSIONS: ClassVar[set[str]] = {
        ".xlsx",
        ".xlsm",
        ".xltx",
        ".xltm",
    }

    def inspect(self, path: str) -> dict[str, Any]:
        file_path = Path(path)
        if file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported Excel file: {file_path.suffix}")
        if not file_path.exists():
            raise FileNotFoundError(file_path)

        try:
            import openpyxl
        except ImportError as exc:
            raise RuntimeError("Excel support requires openpyxl") from exc

        workbook = openpyxl.load_workbook(file_path, read_only=True, data_only=False)
        sheets: list[dict[str, Any]] = []
        for worksheet in workbook.worksheets:
            sheets.append(
                {
                    "name": worksheet.title,
                    "rows": worksheet.max_row,
                    "columns": worksheet.max_column,
                    "dimensions": worksheet.calculate_dimension(),
                }
            )
        workbook.close()
        return {"path": str(file_path), "sheets": sheets}
