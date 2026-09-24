from pathlib import Path

import openpyxl

from noor.web import NoorApplication


def make_workbook(path: Path) -> None:
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Sales"
    sheet.append(["Product", "Sales"])
    sheet.append(["A", 100])
    sheet.append(["B", 200])
    workbook.save(path)


def test_application_executes_inspection_and_verification(tmp_path: Path) -> None:
    workbook_path = tmp_path / "sales.xlsx"
    make_workbook(workbook_path)

    app = NoorApplication(upload_dir=tmp_path / "uploads")
    result = app.execute("Inspect an Excel workbook", str(workbook_path))

    assert result["success"] is True
    assert [node["capability"] for node in result["plan"]] == ["excel.inspect", "result.verify"]
    assert result["executions"][0]["provider"] == "excel.inspect"
    assert result["executions"][-1]["output"]["valid"] is True


def test_application_executes_analysis_workflow(tmp_path: Path) -> None:
    workbook_path = tmp_path / "sales.xlsx"
    make_workbook(workbook_path)

    app = NoorApplication(upload_dir=tmp_path / "uploads")
    result = app.execute("Analyze my Excel data", str(workbook_path))

    assert result["success"] is True
    assert [node["capability"] for node in result["plan"]] == [
        "excel.inspect", "data.profile", "result.verify"
    ]
    profile = result["executions"][1]["output"]
    assert profile["rows"] == 2
    assert profile["columns"] == 2
    assert result["executions"][-1]["output"]["valid"] is True


def test_application_requires_a_workbook_for_excel_operations(tmp_path: Path) -> None:
    app = NoorApplication(upload_dir=tmp_path / "uploads")

    try:
        app.execute("Inspect an Excel workbook")
    except ValueError as exc:
        assert "Attach an Excel workbook" in str(exc)
    else:
        raise AssertionError("Expected a missing workbook error")
