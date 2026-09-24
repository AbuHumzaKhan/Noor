from pathlib import Path

from noor.automation.excel_intelligence import ExcelIntelligenceSkill
from noor.web import NoorApplication


def make_dataset(tmp_path: Path) -> Path:
    path = tmp_path / "sales.csv"
    path.write_text(
        "Product,Category,Sales,Quantity\n"
        "A,Electronics,100,2\n"
        "B,Electronics,200,4\n"
        "C,Furniture,50,1\n"
        "B,Electronics,200,4\n"
        "D,Furniture,,3\n",
        encoding="utf-8",
    )
    return path


def test_answer_question_uses_real_dataset_values(tmp_path: Path) -> None:
    dataset = make_dataset(tmp_path)
    skill = ExcelIntelligenceSkill()
    result = skill.answer_question(str(dataset), "What is the total Sales?")

    assert result["verified"] is True
    assert result["evidence"]["sum"] == 550.0
    assert "550.00" in result["answer"]


def test_formula_recommendation_is_version_aware(tmp_path: Path) -> None:
    dataset = make_dataset(tmp_path)
    skill = ExcelIntelligenceSkill()

    modern = skill.recommend_formula(str(dataset), "Which formula should I use for a lookup?", excel_version="2021")
    legacy = skill.recommend_formula(str(dataset), "Which formula should I use for a lookup?", excel_version="2019")

    assert modern["recommended_function"] == "XLOOKUP"
    assert legacy["recommended_function"] == "INDEX+MATCH"
    assert legacy["compatible"] is True


def test_question_generation_uses_schema(tmp_path: Path) -> None:
    dataset = make_dataset(tmp_path)
    skill = ExcelIntelligenceSkill()
    result = skill.generate_questions(str(dataset), limit=10)

    assert result["questions"]
    assert any("Sales" in question for question in result["questions"])


def test_chat_routes_to_intelligence(tmp_path: Path) -> None:
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    source = make_dataset(upload_dir)
    app = NoorApplication(upload_dir=upload_dir)

    result = app.execute("What is the total Sales?", str(source))
    capabilities = [item["capability"] for item in result["executions"]]

    assert "excel.intelligence.answer" in capabilities
    assert result["success"] is True
