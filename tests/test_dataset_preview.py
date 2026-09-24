from pathlib import Path

from noor.web import NoorApplication


def test_dataset_preview_reads_uploaded_csv(tmp_path: Path) -> None:
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    csv_path = upload_dir / "shipments.csv"
    csv_path.write_text("Order,Revenue\nA,100\nB,200\n", encoding="utf-8")

    app = NoorApplication(upload_dir=upload_dir)
    preview = app.preview_dataset(str(csv_path))

    assert preview["filename"] == "shipments.csv"
    assert preview["format"] == "CSV"
    assert preview["rows_returned"] == 2
    assert preview["columns"] == ["Order", "Revenue"]
    assert preview["records"][0]["Revenue"] == 100


def test_dataset_preview_rejects_paths_outside_upload_directory(tmp_path: Path) -> None:
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    outside = tmp_path / "outside.csv"
    outside.write_text("Order,Revenue\nA,100\n", encoding="utf-8")

    app = NoorApplication(upload_dir=upload_dir)

    try:
        app.preview_dataset(str(outside))
    except ValueError as exc:
        assert "only available for files uploaded through Noor" in str(exc)
    else:
        raise AssertionError("Expected the preview path boundary to reject the file")
