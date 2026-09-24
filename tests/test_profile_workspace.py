from pathlib import Path

from noor.web import NoorApplication


def test_profile_dataset_returns_real_quality_signals(tmp_path: Path) -> None:
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    dataset = upload_dir / "quality.csv"
    dataset.write_text(
        "Customer,Revenue,Region\n"
        "A,100,North\n"
        "B,200,South\n"
        "B,200,South\n"
        "C,,North\n",
        encoding="utf-8",
    )

    app = NoorApplication(upload_dir=upload_dir)
    result = app.profile_dataset(str(dataset))

    assert result["rows"] == 4
    assert result["columns"] == 3
    assert result["duplicate_rows"] == 1
    revenue = next(column for column in result["column_profile"] if column["name"] == "Revenue")
    assert revenue["missing_count"] == 1
    assert revenue["missing_pct"] == 25.0


def test_profile_dataset_rejects_path_outside_upload_directory(tmp_path: Path) -> None:
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    outside = tmp_path / "outside.csv"
    outside.write_text("A,B\n1,2\n", encoding="utf-8")

    app = NoorApplication(upload_dir=upload_dir)

    try:
        app.profile_dataset(str(outside))
    except ValueError as exc:
        assert "uploaded through Noor" in str(exc)
    else:
        raise AssertionError("Expected upload-directory boundary validation")
