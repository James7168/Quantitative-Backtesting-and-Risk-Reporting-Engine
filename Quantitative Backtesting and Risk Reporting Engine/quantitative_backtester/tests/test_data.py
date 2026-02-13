from datetime import datetime
from pathlib import Path

import pytest

from backtester.data import load_bars, validate_path


def _write_csv(path: Path, text: str) -> None:
    path.write_text(text, encoding = "utf-8")


def test_validate_path_raises_when_file_missing(tmp_path: Path):
    missing = tmp_path / "missing.csv"
    with pytest.raises(FileNotFoundError, match = "File not found."):
        validate_path(missing)


def test_validate_path_raises_when_path_is_not_file(tmp_path: Path):
    folder = tmp_path / "data"
    folder.mkdir()
    with pytest.raises(ValueError, match = "Path is not a file."):
        validate_path(folder)


def test_load_bars_happy_path_parses_rows(tmp_path: Path):
    csv_path = tmp_path / "bars.csv"
    _write_csv(
        csv_path,
        "\n".join(
            [
                "timestamp,open,high,low,close,volume",
                "2024-01-01T00:00:00,100,110,90,105,10",
                "2024-01-02T00:00:00,105,120,100,115,20",
            ]
        ),
    )

    bars = load_bars(csv_path)

    assert len(bars) == 2
    assert bars[0].timestamp == datetime.fromisoformat("2024-01-01T00:00:00")
    assert str(bars[0].open) == "100"
    assert str(bars[0].high) == "110"
    assert str(bars[0].low) == "90"
    assert str(bars[0].close) == "105"
    assert bars[0].volume == 10


def test_load_bars_raises_when_required_columns_missing(tmp_path: Path):
    csv_path = tmp_path / "bars.csv"
    _write_csv(
        csv_path,
        "\n".join(
            [
                "timestamp,open,high,low,close",
                "2024-01-01T00:00:00,100,110,90,105",
            ]
        ),
    )

    with pytest.raises(ValueError, match = "Missing required columns."):
        load_bars(csv_path)


def test_load_bars_raises_when_file_is_empty_after_header(tmp_path: Path):
    csv_path = tmp_path / "bars.csv"
    _write_csv(csv_path, "timestamp,open,high,low,close,volume\n")

    with pytest.raises(ValueError, match = "No bar data located."):
        load_bars(csv_path)


def test_load_bars_raises_with_row_number_on_invalid_timestamp(tmp_path: Path):
    csv_path = tmp_path / "bars.csv"
    _write_csv(
        csv_path,
        "\n".join(
            [
                "timestamp,open,high,low,close,volume",
                "NOT_A_TIMESTAMP,100,110,90,105,10",
            ]
        ),
    )

    with pytest.raises(ValueError, match = "Invalid data at row: 2."):
        load_bars(csv_path)


def test_load_bars_raises_with_row_number_on_invalid_numeric_field(tmp_path: Path):
    csv_path = tmp_path / "bars.csv"
    _write_csv(
        csv_path,
        "\n".join(
            [
                "timestamp,open,high,low,close,volume",
                "2024-01-01T00:00:00,100,110,90,NOT_A_DECIMAL,10",
            ]
        ),
    )

    with pytest.raises(ValueError, match = "Invalid data at row: 2."):
        load_bars(csv_path)


def test_load_bars_raises_when_duplicate_timestamps_detected(tmp_path: Path):
    csv_path = tmp_path / "bars.csv"
    _write_csv(
        csv_path,
        "\n".join(
            [
                "timestamp,open,high,low,close,volume",
                "2024-01-01T00:00:00,100,110,90,105,10",
                "2024-01-01T00:00:00,105,115,95,110,12",
            ]
        ),
    )

    with pytest.raises(ValueError, match = "Duplicate timestamps detected."):
        load_bars(csv_path)


def test_load_bars_raises_when_bars_not_sorted(tmp_path: Path):
    csv_path = tmp_path / "bars.csv"
    _write_csv(
        csv_path,
        "\n".join(
            [
                "timestamp,open,high,low,close,volume",
                "2024-01-02T00:00:00,105,120,100,115,20",
                "2024-01-01T00:00:00,100,110,90,105,10",
            ]
        ),
    )

    with pytest.raises(ValueError, match = "Bars must be sorted by ascending timestamp."):
        load_bars(csv_path)


def test_load_bars_raises_when_bar_validation_fails(tmp_path: Path):
    csv_path = tmp_path / "bars.csv"
    _write_csv(
        csv_path,
        "\n".join(
            [
                "timestamp,open,high,low,close,volume",
                "2024-01-01T00:00:00,-1,10,0.5,5,10",
            ]
        ),
    )

    with pytest.raises(ValueError, match = "Invalid data at row: 2."):
        load_bars(csv_path)