from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar


class ExcelSkill:
    """Deterministic Excel operations exposed to Noor's V1 Orchestra.

    V1 deliberately uses openpyxl and never executes workbook macros. Mutating
    operations are explicit and return structured metadata for verification.
    """

    SUPPORTED_EXTENSIONS: ClassVar[set[str]] = {
        ".xlsx",
        ".xlsm",
        ".xltx",
        ".xltm",
    }
    DEFAULT_MAX_ROWS: ClassVar[int] = 1000
    DEFAULT_MAX_COLUMNS: ClassVar[int] = 100

    def _validate_path(self, path: str) -> Path:
        file_path = Path(path).expanduser()
        if file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported Excel file: {file_path.suffix}")
        if not file_path.exists():
            raise FileNotFoundError(file_path)
        if not file_path.is_file():
            raise ValueError(f"Excel path is not a file: {file_path}")
        return file_path

    @staticmethod
    def _openpyxl():
        try:
            import openpyxl
        except ImportError as exc:
            raise RuntimeError("Excel support requires openpyxl") from exc
        return openpyxl

    def inspect(self, path: str) -> dict[str, Any]:
        file_path = self._validate_path(path)
        openpyxl = self._openpyxl()
        workbook = openpyxl.load_workbook(file_path, read_only=True, data_only=False)
        try:
            sheets = [
                {
                    "name": worksheet.title,
                    "rows": worksheet.max_row,
                    "columns": worksheet.max_column,
                    "dimensions": worksheet.calculate_dimension(),
                }
                for worksheet in workbook.worksheets
            ]
            return {"path": str(file_path), "sheets": sheets}
        finally:
            workbook.close()

    def read_sheet(
        self,
        path: str,
        sheet_name: str,
        max_rows: int = DEFAULT_MAX_ROWS,
        max_columns: int = DEFAULT_MAX_COLUMNS,
    ) -> dict[str, Any]:
        if max_rows < 1 or max_columns < 1:
            raise ValueError("max_rows and max_columns must be positive")
        file_path = self._validate_path(path)
        openpyxl = self._openpyxl()
        workbook = openpyxl.load_workbook(file_path, read_only=True, data_only=False)
        try:
            if sheet_name not in workbook.sheetnames:
                raise KeyError(f"Worksheet not found: {sheet_name}")
            worksheet = workbook[sheet_name]
            values: list[list[Any]] = []
            for row in worksheet.iter_rows(
                min_row=1,
                max_row=min(max_rows, worksheet.max_row),
                min_col=1,
                max_col=min(max_columns, worksheet.max_column),
                values_only=True,
            ):
                values.append(list(row))
            return {
                "path": str(file_path),
                "sheet": sheet_name,
                "rows_returned": len(values),
                "columns_returned": max((len(row) for row in values), default=0),
                "values": values,
            }
        finally:
            workbook.close()

    def write_cells(
        self,
        path: str,
        sheet_name: str,
        cells: dict[str, Any],
        output_path: str | None = None,
    ) -> dict[str, Any]:
        if not cells:
            raise ValueError("write_cells requires at least one cell")
        source = self._validate_path(path)
        destination = Path(output_path).expanduser() if output_path else source
        if destination.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported Excel output: {destination.suffix}")

        openpyxl = self._openpyxl()
        keep_vba = source.suffix.lower() in {".xlsm", ".xltm"}
        workbook = openpyxl.load_workbook(source, read_only=False, data_only=False, keep_vba=keep_vba)
        try:
            if sheet_name not in workbook.sheetnames:
                raise KeyError(f"Worksheet not found: {sheet_name}")
            worksheet = workbook[sheet_name]
            for coordinate, value in cells.items():
                worksheet[coordinate] = value
            workbook.save(destination)
        finally:
            workbook.close()

        return {
            "source": str(source),
            "output": str(destination),
            "sheet": sheet_name,
            "cells_written": len(cells),
            "coordinates": sorted(cells),
        }
