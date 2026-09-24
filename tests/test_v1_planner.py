from noor.automation.v1_planner import V1Planner


def test_generic_dataset_profile_plan() -> None:
    graph = V1Planner().plan("Profile my data", "/tmp/sales.csv")
    assert [node.capability for node in graph.nodes] == ["data.inspect", "data.profile", "result.verify"]


def test_excel_search_plan() -> None:
    graph = V1Planner().plan("Search this workbook for Revenue", "/tmp/sales.xlsx", "Sales")
    assert graph.nodes[0].capability == "excel.search"
    assert graph.nodes[0].inputs["query"] == "this workbook for Revenue"


def test_excel_formula_validation_plan() -> None:
    graph = V1Planner().plan("Validate formula =SUM(B2:B100)", "/tmp/sales.xlsx")
    assert graph.nodes[0].capability == "excel.formula.validate"
