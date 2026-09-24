from pathlib import Path

import openpyxl

from noor.automation.excel_advanced import AdvancedExcelSkill


def workbook_file(tmp_path: Path) -> Path:
    path = tmp_path / "workbook.xlsx"
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Sales"
    sheet.append(["Product", "Revenue"])
    sheet.append(["A", 100])
    sheet.append(["B", 200])
    sheet.append(["A", 100])
    workbook.save(path)
    workbook.close()
    return path


def test_formula_validation_and_explanation() -> None:
    validator = AdvancedExcelSkill()
    assert validator.validate_formula("=SUM(B2:B10)")["valid"] is True
    assert validator.validate_formula("=SUM(B2:B10")["valid"] is False
    explanation = validator.explain_formula("=SUM(B2:B10)")
    assert explanation["function"] == "SUM"


def test_workbook_search(tmp_path: Path) -> None:
    path = workbook_file(tmp_path)
    result = AdvancedExcelSkill().search(str(path), "Product")
    assert result["matches"][0]["cell"] == "A1"


def test_freeze_and_filter(tmp_path: Path) -> None:
    path = workbook_file(tmp_path)
    skill = AdvancedExcelSkill()
    skill.freeze(str(path), "Sales", "A2")
    skill.set_filter(str(path), "Sales", "A1:B4")
    workbook = openpyxl.load_workbook(path)
    sheet = workbook["Sales"]
    assert str(sheet.freeze_panes) == "A2"
    assert sheet.auto_filter.ref == "A1:B4"
    workbook.close()
