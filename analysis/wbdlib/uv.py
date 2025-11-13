"""Helpers for working with unified-view survey data."""

from __future__ import annotations

import csv
import re
from pathlib import Path
import pandas as pd


GROUP_PATTERN = re.compile(r"group\s+([a-f])", re.IGNORECASE)


def first_segment(value: object | None) -> str | None:
    """Return the first comma-delimited segment for the provided value."""
    if value is None:
        return None
    text = str(value)
    if not text:
        return None
    return text.split(",", 1)[0].strip() or None


def extract_group_letter(value: object | None) -> str | None:
    """Extract the group letter from a free-form value like "Group A - Foo"."""
    if value is None:
        return None
    match = GROUP_PATTERN.search(str(value))
    if match:
        return match.group(1).upper()
    return None


def extract_group_letter_from_path(path: str | Path) -> str:
    """Infer the group letter using the survey export folder structure."""
    path_obj = Path(path)
    for part in path_obj.parts:
        if part.lower().startswith("group "):
            candidate = part.split(" ")[-1].strip().strip("/")
            if candidate:
                return candidate[0].upper()
    raise ValueError(f"Could not determine group letter from path: {path_obj}")


def load_survey_file(path: str | Path) -> pd.DataFrame:
    """Load a raw survey file, preserving text columns exactly."""
    return pd.read_csv(
        path,
        sep="\t",
        dtype=str,
        engine="python",
        quoting=csv.QUOTE_NONE,
        encoding="utf-8",
        on_bad_lines="warn",
    )


def rename_survey_columns(
    df: pd.DataFrame,
    rename_map: pd.DataFrame,
    group_letter: str,
) -> pd.DataFrame:
    """Apply group-specific column renaming and return only mapped columns."""
    if (
        "raw_column" not in rename_map.columns
        or "target_column" not in rename_map.columns
    ):
        raise KeyError(
            "rename_map must contain 'raw_column' and 'target_column' columns"
        )
    filtered = rename_map.copy()
    filtered["group"] = filtered.get("group", group_letter)
    filtered["group"] = filtered["group"].astype(str).str.upper().str.strip()
    group_letter = group_letter.upper()
    group_rows = filtered.loc[filtered["group"] == group_letter]
    rename_dict = group_rows.set_index("raw_column")["target_column"]
    rename_dict = rename_dict.astype(str)
    rename_dict = rename_dict.str.strip().to_dict()
    renamed = df.rename(columns=rename_dict)
    ordered_columns = []
    for raw_col in group_rows["target_column"].astype(str):
        cleaned = raw_col.strip()
        if cleaned in renamed.columns:
            ordered_columns.append(cleaned)
    return renamed.loc[:, ordered_columns]


__all__ = [
    "extract_group_letter",
    "extract_group_letter_from_path",
    "first_segment",
    "load_survey_file",
    "rename_survey_columns",
]
