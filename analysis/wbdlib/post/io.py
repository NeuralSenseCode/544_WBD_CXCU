"""I/O and parsing helpers for post questionnaire data."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

import numpy as np
import pandas as pd


_CODE_PATTERN = re.compile(r"^\s*([0-9]+(?:\.[0-9]+)*)")


def extract_question_code(text: str | float | None) -> str | None:
    """Return the leading numeric code segment from the provided text."""
    if text is None or (isinstance(text, float) and np.isnan(text)):
        return None
    match = _CODE_PATTERN.match(str(text))
    return match.group(1) if match else None


def merge_duplicate_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Collapse duplicate columns in a post questionnaire export."""
    def _sanitize(value: object) -> object:
        if pd.isna(value):
            return np.nan
        if isinstance(value, str):
            cleaned = value.strip()
            return cleaned if cleaned else np.nan
        return value

    merged: dict[str, pd.Series] = {}
    column_order: list[str] = []
    for column in df.columns:
        normalized = re.sub(r"\s+", " ", str(column)).strip()
        series = df[column].astype("object").map(_sanitize)
        if normalized not in merged:
            merged[normalized] = series
            column_order.append(normalized)
        else:
            merged[normalized] = merged[normalized].combine_first(series)
    return pd.DataFrame({name: merged[name] for name in column_order})


def load_post_questionnaire(path: str | Path) -> pd.DataFrame:
    """Load a post questionnaire CSV while preserving raw text columns."""
    return pd.read_csv(path, dtype=str)


@dataclass(frozen=True)
class PostFile:
    path: Path
    group_letter: str | None


def find_post_files(root: Path) -> list[PostFile]:
    """Discover post questionnaire files under the provided root directory."""
    if not root.exists():
        raise FileNotFoundError(
            f"Post questionnaire directory not found at {root}."
        )
    files: list[PostFile] = []
    for path in sorted(
        p
        for p in root.rglob("*.csv")
        if p.is_file() and not p.name.startswith("~$")
    ):
        match = re.search(r"Group\s+([A-F])", path.stem, re.IGNORECASE)
        group_letter = match.group(1).upper() if match else None
        files.append(PostFile(path=path, group_letter=group_letter))
    if not files:
        raise FileNotFoundError(
            f"No post questionnaire CSV files found under {root}."
        )
    return files


__all__ = [
    "PostFile",
    "extract_question_code",
    "find_post_files",
    "load_post_questionnaire",
    "merge_duplicate_columns",
]
