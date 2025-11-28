"""I/O utilities shared across notebooks."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Mapping, Sequence, Tuple

import pandas as pd


def _timestamped_fallback(path: Path) -> Path:
    timestamp = pd.Timestamp.utcnow().strftime("%Y%m%d%H%M%S")
    suffix = f"{path.stem}_{timestamp}{path.suffix}"
    return path.with_name(suffix)


def safe_write_csv(df: pd.DataFrame, path: str | Path) -> Path:
    """Write DataFrame to CSV; retry with timestamped suffix if needed."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    def _write_csv(target: Path) -> None:
        df.to_csv(target, index=False)

    try:
        _write_csv(output_path)
        return output_path
    except PermissionError:
        fallback = _timestamped_fallback(output_path)
        _write_csv(fallback)
        print(
            "PermissionError writing "
            f"{output_path}, wrote to {fallback} instead"
        )
        return fallback


SheetPairs = Sequence[Tuple[str, pd.DataFrame]]


def _normalise_sheet_pairs(
    sheets: Mapping[str, pd.DataFrame] | Iterable[Tuple[str, pd.DataFrame]]
) -> SheetPairs:
    if isinstance(sheets, Mapping):
        items = list(sheets.items())
    else:
        items = list(sheets)
    if not items:
        raise ValueError(
            "At least one sheet must be provided when exporting Excel data."
        )
    return [(str(name), frame) for name, frame in items]


def safe_write_excel(
    sheets: Mapping[str, pd.DataFrame] | Iterable[Tuple[str, pd.DataFrame]],
    path: str | Path,
    *,
    metadata: Mapping[str, object] | None = None,
    index: bool = False,
    engine: str = "xlsxwriter",
) -> Path:
    """Persist multiple DataFrames in a single workbook with retry support."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet_pairs = _normalise_sheet_pairs(sheets)

    def _write_excel(target: Path) -> None:
        with pd.ExcelWriter(target, engine=engine) as writer:
            for idx, (sheet_name, frame) in enumerate(sheet_pairs, start=1):
                cleaned_name = (sheet_name or f"sheet_{idx}")[:31]
                frame.to_excel(writer, sheet_name=cleaned_name, index=index)
            if metadata:
                metadata_frame = pd.DataFrame(
                    {
                        "field": list(metadata.keys()),
                        "value": [metadata[key] for key in metadata],
                    }
                )
                metadata_frame.to_excel(
                    writer, sheet_name="metadata", index=False
                )

    try:
        _write_excel(output_path)
        return output_path
    except PermissionError:
        fallback = _timestamped_fallback(output_path)
        _write_excel(fallback)
        print(
            "PermissionError writing "
            f"{output_path}, wrote to {fallback} instead"
        )
        return fallback


__all__ = ["safe_write_csv", "safe_write_excel"]
