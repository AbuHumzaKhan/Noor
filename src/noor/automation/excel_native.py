from __future__ import annotations

from pathlib import Path
from typing import Any


class NativeExcelSkill:
    """Optional Windows desktop Excel automation adapter.

    Uses Excel's own object model when Microsoft Excel and pywin32 are available.
    The adapter never runs macros from the workbook and writes to a new output
    file by default so the original workbook remains unchanged.
    """

    SUPPORTED = {".xlsx", ".xlsm", ".xltx", ".xltm"}
    AGGREGATIONS = {
        "sum": -4157,
        "average": -4106,
        "count": -4112,
        "max": -4136,
        "min": -4139,
    }
    ROW_FIELD = 1
    COLUMN_FIELD = 2
    DATA_FIELD = 4

    @staticmethod
    def _excel():
        try:
            import win32com.client as win32
        except ImportError as exc:
            raise RuntimeError("Native Excel automation requires pywin32. The regular Noor analytics engine does not require it.") from exc
        try:
            return win32.DispatchEx("Excel.Application")
        except Exception as exc:
            raise RuntimeError("Microsoft Excel desktop could not be started on this Windows machine.") from exc

    @staticmethod
    def _output_path(source: Path, output_path: str | None, suffix: str) -> Path:
        if output_path:
            return Path(output_path).expanduser().resolve()
        return source.with_name(f"{source.stem}_{suffix}{source.suffix}")

    def create_pivot_table(
        self,
        path: str,
        row_field: str,
        value_field: str,
        column_field: str | None = None,
        aggfunc: str = "sum",
        sheet_name: str | None = None,
        destination_sheet: str = "Noor_Pivot",
        output_path: str | None = None,
    ) -> dict[str, Any]:
        source = Path(path).expanduser().resolve()
        if source.suffix.lower() not in self.SUPPORTED:
            raise ValueError(f"Native PivotTable requires an Excel workbook: {source.suffix}")
        if not source.is_file(): raise FileNotFoundError(source)
        if aggfunc not in self.AGGREGATIONS: raise ValueError(f"Unsupported PivotTable aggregation: {aggfunc}")

        output = self._output_path(source, output_path, "NoorPivot")
        excel = self._excel()
        workbook = None
        try:
            excel.Visible = False
            excel.DisplayAlerts = False
            workbook = excel.Workbooks.Open(str(source))
            source_sheet = workbook.Worksheets(sheet_name) if sheet_name else workbook.ActiveSheet
            source_range = source_sheet.UsedRange
            if source_range.Rows.Count < 2 or source_range.Columns.Count < 2:
                raise ValueError("The worksheet does not contain enough tabular data for a PivotTable")

            try:
                destination = workbook.Worksheets(destination_sheet)
                destination.Cells.Clear()
            except Exception:
                destination = workbook.Worksheets.Add(After=workbook.Worksheets(workbook.Worksheets.Count))
                destination.Name = destination_sheet[:31]

            cache = workbook.PivotCaches().Create(1, source_range.Address(True, True, 1, True))
            pivot = cache.CreatePivotTable(destination.Range("A3"), "NoorPivotTable", True)
            pivot.PivotFields(row_field).Orientation = self.ROW_FIELD
            pivot.PivotFields(row_field).Position = 1
            if column_field:
                pivot.PivotFields(column_field).Orientation = self.COLUMN_FIELD
                pivot.PivotFields(column_field).Position = 1
            data_field = pivot.AddDataField(pivot.PivotFields(value_field), f"{aggfunc.title()} of {value_field}", self.AGGREGATIONS[aggfunc])
            data_field.NumberFormat = "#,##0.00"
            destination.Range("A1").Value = "Noor PivotTable"
            destination.Range("A2").Value = f"Source: {source_sheet.Name}"
            destination.Columns.AutoFit()
            workbook.SaveAs(str(output))
            return {
                "output": str(output), "source": str(source), "sheet": source_sheet.Name,
                "pivot_sheet": destination.Name, "row_field": row_field, "value_field": value_field,
                "column_field": column_field, "aggregation": aggfunc, "native": True,
            }
        finally:
            if workbook is not None:
                try: workbook.Close(SaveChanges=False)
                except Exception: pass
            try: excel.Quit()
            except Exception: pass

    def create_chart(
        self,
        path: str,
        sheet_name: str,
        source_range: str,
        chart_type: str = "column",
        output_path: str | None = None,
    ) -> dict[str, Any]:
        source = Path(path).expanduser().resolve()
        if source.suffix.lower() not in self.SUPPORTED: raise ValueError("Chart automation requires an Excel workbook")
        output = self._output_path(source, output_path, "NoorChart")
        excel = self._excel()
        workbook = None
        chart_map = {"column": 51, "bar": 57, "line": 4, "pie": 5, "scatter": -4169}
        if chart_type not in chart_map: raise ValueError(f"Unsupported chart type: {chart_type}")
        try:
            excel.Visible = False
            excel.DisplayAlerts = False
            workbook = excel.Workbooks.Open(str(source))
            sheet = workbook.Worksheets(sheet_name)
            chart_object = sheet.ChartObjects().Add(320, 30, 640, 360)
            chart = chart_object.Chart
            chart.SetSourceData(sheet.Range(source_range))
            chart.ChartType = chart_map[chart_type]
            chart.HasTitle = True
            chart.ChartTitle.Text = f"Noor — {chart_type.title()} Chart"
            workbook.SaveAs(str(output))
            return {"output": str(output), "sheet": sheet_name, "source_range": source_range, "chart_type": chart_type, "native": True}
        finally:
            if workbook is not None:
                try: workbook.Close(SaveChanges=False)
                except Exception: pass
            try: excel.Quit()
            except Exception: pass
