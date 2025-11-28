"""Formatting helpers shared across analysis notebooks."""

from __future__ import annotations

import re
import unicodedata
from numbers import Number
from typing import Iterable

import numpy as np
import pandas as pd


def _coerce_finite_float(value: object) -> float | None:
    """Return value as a finite float when possible."""
    try:
        numeric = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if not np.isfinite(numeric):
        return None
    return numeric


def _fmt_stat(
    value: object,
    pattern: str = "{:.3f}",
    placeholder: str = "NA",
) -> str:
    """Format a statistic while gracefully handling invalid values."""
    if value is None:
        return placeholder
    if isinstance(value, Number):
        numeric = _coerce_finite_float(value)
        if numeric is None:
            return placeholder
        return pattern.format(numeric)
    numeric = _coerce_finite_float(value)
    if numeric is None:
        return placeholder
    return pattern.format(numeric)


def format_percent(value: object, decimals: int = 0) -> str:
    """Return a percentage string for a 0-1 scaled value."""
    numeric = _coerce_finite_float(value)
    if numeric is None:
        return "NA"
    return f"{numeric * 100:.{decimals}f}%"


def format_value(value: object, decimals: int = 0) -> str:
    """Return a percentage string for a 0-1 scaled value."""
    numeric = _coerce_finite_float(value)
    if numeric is None:
        return "NA"
    return f"{numeric:.{decimals}f}"


def percentage_point_phrase(
    long_value: object,
    short_value: object,
    decimals: int = 0,
) -> str:
    """Describe the percentage-point shift between long and short means."""
    long_numeric = _coerce_finite_float(long_value)
    short_numeric = _coerce_finite_float(short_value)
    if long_numeric is None or short_numeric is None:
        return "an indeterminate difference"
    diff = (long_numeric - short_numeric) * 100
    direction = "greater" if diff >= 0 else "lower"
    return f"{abs(diff):.{decimals}f}% {direction}"


def percentage_point_phrase_value(
    long_value: object,
    short_value: object,
    decimals: int = 0,
) -> str:
    """Describe the percentage-point shift between long and short means."""
    long_numeric = _coerce_finite_float(long_value)
    short_numeric = _coerce_finite_float(short_value)
    if long_numeric is None or short_numeric is None:
        return "an indeterminate difference"
    diff = (long_numeric - short_numeric)
    direction = "greater" if diff >= 0 else "lower"
    return f"{abs(diff):.{decimals}f} {direction}"


def format_p_value(p_value: object) -> str:
    """Format p-values using the requested presentation style."""
    numeric = _coerce_finite_float(p_value)
    if numeric is None:
        return "p=NA"
    if numeric < 0.001:
        return "p<0.001"
    if numeric < 0.01:
        return f"p={numeric:.3f}"
    return f"p={numeric:.3f}"


def print_long_short_summary(
    label: str,
    long_mean: object,
    short_mean: object,
    p_value: object | None = None,
    extra_note: str | None = None,
    decimals: int = 0,
) -> None:
    """Print a one-liner comparing long vs short form results."""
    long_txt = format_percent(long_mean, decimals)
    short_txt = format_percent(short_mean, decimals)
    diff_phrase = percentage_point_phrase(long_mean, short_mean, decimals)
    sig_txt = (
        format_p_value(p_value)
        if p_value is not None
        else (extra_note or "")
    )
    if sig_txt:
        sig_txt = f" ({sig_txt})"
    print(
        f"{label}: Long form ({long_txt}) showed {diff_phrase} "
        f"than short form ({short_txt}){sig_txt}."
    )


def print_long_short_summary_value(
    label: str,
    long_mean: object,
    short_mean: object,
    p_value: object | None = None,
    extra_note: str | None = None,
    decimals: int = 0,
) -> None:
    """Print a one-liner comparing long vs short form results."""
    long_txt = format_value(long_mean, decimals)
    short_txt = format_value(short_mean, decimals)
    diff_phrase = percentage_point_phrase_value(
        long_mean, short_mean, decimals
    )
    sig_txt = (
        format_p_value(p_value)
        if p_value is not None
        else (extra_note or "")
    )
    if sig_txt:
        sig_txt = f" ({sig_txt})"
    print(
        f"{label}: Long form ({long_txt}) showed {diff_phrase} "
        f"than short form ({short_txt}){sig_txt}."
    )


def to_percent_table(
    frame: pd.DataFrame,
    percent_columns: Iterable[str],
    decimals: int = 0,
) -> pd.DataFrame:
    """Render the specified columns as percentage strings."""
    table = frame.copy()
    for column in percent_columns:
        if column in table.columns:
            table[column] = table[column].apply(
                lambda val: format_percent(val, decimals)
            )
    return table


def significance_label(p_value: float) -> str:
    """Return a compact significance marker for p-values."""
    numeric = _coerce_finite_float(p_value)
    if numeric is None:
        return ""
    if numeric <= 0.001:
        return "**"
    if numeric <= 0.05:
        return "*"
    return ""


_SAFE_CHAR_RE = re.compile(r"[^A-Za-z0-9._-]+")
_DELIM_RE = re.compile(r"[_-]{2,}")


def _slugify_component(value: str, placeholder: str) -> str:
    """Return a filesystem-friendly token derived from ``value``."""
    text = str(value or "").strip()
    if not text:
        return placeholder
    ascii_value = unicodedata.normalize("NFKD", text)
    ascii_value = ascii_value.encode("ascii", "ignore").decode("ascii")
    ascii_value = _SAFE_CHAR_RE.sub("_", ascii_value)
    ascii_value = _DELIM_RE.sub("_", ascii_value)
    ascii_value = ascii_value.strip("._-")
    ascii_value = ascii_value.lower()
    return ascii_value or placeholder


def slugify_filename(
    value: str,
    *,
    suffix: str | None = None,
    placeholder: str = "plot",
    max_length: int = 120,
) -> str:
    """Convert ``value`` into a safe filename stem.

    Parameters
    ----------
    value:
        String to convert into a slug.
    suffix:
        Optional suffix that will be appended using ``__`` as delimiter.
    placeholder:
        Token to fall back to when ``value`` collapses to an empty string.
    max_length:
        Maximum number of characters returned (excludes extension callers add).
    """

    tokens = [_slugify_component(value, placeholder)]
    if suffix:
        tokens.append(_slugify_component(suffix, "extra"))
    slug = "__".join(token for token in tokens if token)
    if len(slug) > max_length:
        slug = slug[:max_length].rstrip("._-")
    return slug or placeholder


__all__ = [
    "_fmt_stat",
    "format_percent",
    "percentage_point_phrase",
    "format_p_value",
    "print_long_short_summary",
    "to_percent_table",
    "significance_label",
    "slugify_filename",
]
