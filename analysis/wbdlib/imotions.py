"""Utilities for working with iMotions sensor exports."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Tuple

import pandas as pd


def extract_imotions_metadata(
    path: str | Path,
    metadata: Iterable[str] | None = None,
) -> Tuple[dict[str, str], int]:
    """Read leading metadata rows from an iMotions CSV file."""
    requested = {item for item in metadata or []}
    filter_requested = bool(metadata)
    path_obj = Path(path)
    meta_lines: list[str] = []
    header_rows = 0
    with path_obj.open("r", encoding="latin1") as handle:
        for line in handle:
            first_cell = line.split(",", 1)[0]
            if "#" in first_cell:
                meta_lines.append(line)
                header_rows += 1
            else:
                break
    meta_dict: dict[str, str] = {}
    for raw_line in meta_lines:
        segments = raw_line.strip().split("#", 1)
        if len(segments) < 2:
            continue
        cleaned = segments[1]
        parts = cleaned.split(",")
        if len(parts) <= 1:
            continue
        key = parts[0].strip()
        value = ",".join(parts[1:]).strip()
        if not filter_requested or key in requested:
            meta_dict[key] = value
    return meta_dict, header_rows


def read_imotions_metadata(
    path: str | Path,
    metadata: Iterable[str] | None = None,
) -> dict[str, str]:
    """Return the requested metadata fields from an iMotions CSV file."""
    meta_dict, _ = extract_imotions_metadata(path, metadata)
    return meta_dict


def read_imotions(
    path: str | Path,
    metadata: Iterable[str] | None = None,
    **read_csv_kwargs,
) -> tuple[pd.DataFrame, dict[str, str]]:
    """Load an iMotions CSV and return the data alongside optional metadata."""
    meta_dict, header_rows = extract_imotions_metadata(path, metadata)
    csv_kwargs: dict[str, Any] = dict(read_csv_kwargs)
    csv_kwargs.setdefault("low_memory", True)
    df = pd.read_csv(path, header=header_rows, **csv_kwargs)
    return df, meta_dict


__all__ = [
    "extract_imotions_metadata",
    "read_imotions",
    "read_imotions_metadata",
]
