from csv import DictReader
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from backtester.models import Bar


def validate_path(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    if not path.is_file():
        raise ValueError(f"Path is not a file: {path}")


def load_bars(path: Path) -> list[Bar]:
    """
    Load historical OHLCV bars from a local CSV file into Bar domain objects.
    Note: Input must already be sorted.

    Args:
        path: Local filesystem Path to a CSV containing columns:
              timestamp, open, high, low, close, volume.

    Returns:
        A list of Bar objects in ascending timestamp order.

    Raises:
        FileNotFoundError: If the path does not exist.
        ValueError: If the path is not a file, required columns are missing, any row is invalid,
            the file is empty, timestamps are duplicated, or bars are not sorted.
    
    """
    validate_path(path)
    
    bars: list[Bar] = []

    with path.open(newline = "") as fh:
        reader = DictReader(fh)

        fieldnames = reader.fieldnames or []
        required_columns = {"timestamp", "open", "high", "low", "close", "volume"}
        if not required_columns.issubset(fieldnames):
            missing = required_columns - set(fieldnames)
            raise ValueError(f"Missing required columns: {missing}")
        
        # Row numbers begin at 2, this is because row 1 contains the header.
        for row_num, row in enumerate(reader, start = 2):
            try:
                ts = datetime.fromisoformat(row["timestamp"])

                open_ = Decimal(row["open"])
                high = Decimal(row["high"])
                low = Decimal(row["low"])
                close = Decimal(row["close"])
                volume = int(row["volume"])

                bar = Bar(timestamp = ts, open = open_, high = high, low = low, close = close, volume = volume)
                bars.append(bar)
            
            except Exception as exc:
                # Adding row context to this exception for clarity.
                raise ValueError(f"Invalid data at row: {row_num}: {exc}") from exc
    
    if not bars:
        raise ValueError("No bar data located.")
            
    timestamps = [b.timestamp for b in bars]
    if len(timestamps) != len(set(timestamps)):
        raise ValueError("Duplicate timestamps detected in input.")
    
    if timestamps != sorted(timestamps):
        raise ValueError("Bars must be sorted by ascending timestamp.")
    
    return bars