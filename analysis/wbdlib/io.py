"""I/O utilities shared across notebooks."""

from __future__ import annotations

from pathlib import Path
import pandas as pd


def safe_write_csv(df: pd.DataFrame, path: str | Path) -> Path:
    """Write DataFrame to CSV; retry with timestamped suffix if needed."""
    output_path = Path(path)
    try:
        df.to_csv(output_path, index=False)
        return output_path
    except PermissionError:
        timestamp = pd.Timestamp.utcnow().strftime("%Y%m%d%H%M%S")
        suffix = f"{output_path.stem}_{timestamp}{output_path.suffix}"
        fallback = output_path.with_name(suffix)
        df.to_csv(fallback, index=False)
        message = (
            "PermissionError writing "
            f"{output_path}, wrote to {fallback} instead"
        )
        print(message)
        return fallback


__all__ = ["safe_write_csv"]
