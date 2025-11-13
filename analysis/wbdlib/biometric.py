"""Biometric data helpers shared across notebooks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

import numpy as np
import pandas as pd

# Sensors present in the unified biometric extract. We only analyse a subset,
# but the parser understands the full catalogue so the helpers remain reusable.
KNOWN_SENSORS: tuple[str, ...] = (
    "EEG",
    "ET",
    "FAC",
    "GSR",
    "Post",
    "Screening",
    "Survey",
)

# Stats observed in the biometric UV. We rely on the longest suffix match to
# separate metric and stat tokens when parsing column headers.
KNOWN_STATS: tuple[str, ...] = (
    "AUC",
    "Binary",
    "C1",
    "C1_Count",
    "C1_Normalized",
    "Corrected",
    "Count",
    "E1",
    "E10",
    "E11",
    "E12",
    "E13",
    "E14",
    "E15",
    "E17",
    "E18",
    "E19",
    "E2",
    "E20",
    "E21",
    "E22",
    "E3",
    "E4",
    "E5",
    "E6",
    "E7",
    "E8",
    "E9",
    "F1",
    "F2",
    "F3",
    "Mean",
    "Normalized",
    "NormalizedCorrected",
    "NormalizedMean",
    "OpenEndedKMS",
    "OpenEndedSum",
    "PerMinute",
    "Q01",
    "Q02",
    "Q03",
    "Q04",
    "Q05",
    "Q06",
    "Q07",
    "Q08",
    "Q09",
    "Q1-1",
    "Q1-2",
    "Q10",
    "Q10-1",
    "Q10-2",
    "Q11",
    "Q11-1",
    "Q11-2",
    "Q12",
    "Q12-1",
    "Q12-2",
    "Q2-1",
    "Q2-2",
    "Q3-1",
    "Q3-2",
    "Q4-1",
    "Q4-2",
    "Q5-1",
    "Q5-2",
    "Q6-1",
    "Q6-2",
    "Q7-1",
    "Q7-2",
    "Q8-1",
    "Q8-2",
    "Q9-1",
    "Q9-2",
    "Rate",
    "Sum",
    "WBD1",
    "WBD2",
    "WBD3",
    "WBD4",
    "WBD5",
)

# Common title corrections. Keys are stored in lower case for quick lookups.
TITLE_FIXES: Mapping[str, str] = {
    "abbot elementary": "Abbott Elementary",
}

FORM_ORDER: tuple[str, ...] = ("Short", "Long")


@dataclass(frozen=True)
class BiometricHeader:
    """Structured representation of a biometric column header."""

    form: str
    title: str
    sensor: str
    metric: str
    stat: str
    column: str


def _clean_whitespace(text: str) -> str:
    """Collapse internal whitespace and strip the input string."""

    return " ".join(text.split())


def _normalise_title(text: str) -> str:
    """Apply canonical casing fixes to a title token."""

    cleaned = _clean_whitespace(text.replace("_", " "))
    lower = cleaned.lower()
    return TITLE_FIXES.get(lower, cleaned)


def _stat_from_tokens(tokens: Sequence[str], *, known_stats: Sequence[str]) -> tuple[str, Sequence[str]] | None:
    """Return (stat, metric_tokens) given the tail tokens of a header."""

    if len(tokens) < 2:
        return None
    stats_set = set(known_stats)
    for size in range(1, len(tokens) + 1):
        stat_candidate = "_".join(tokens[-size:])
        if stat_candidate in stats_set:
            metric_tokens = tokens[:-size]
            if metric_tokens:
                return stat_candidate, metric_tokens
    # Fall back to treating the final token as the stat when no match found.
    stat_candidate = tokens[-1]
    metric_tokens = tokens[:-1]
    if metric_tokens:
        return stat_candidate, metric_tokens
    return None


def parse_biometric_header(
    column: str,
    *,
    sensors: Sequence[str] = KNOWN_SENSORS,
    known_stats: Sequence[str] = KNOWN_STATS,
) -> BiometricHeader | None:
    """Parse a UV biometric column into its constituent components.

    Parameters
    ----------
    column:
        Column header in ``{form}_{title}_{sensor}_{metric}_{stat}`` format.
    sensors:
        Iterable of allowed sensor labels. The first match after the form token
        is treated as the sensor boundary.
    known_stats:
        Catalogue of recognised stat suffixes. The parser uses the longest
        matching suffix to keep metric names intact when underscores appear in
        stats (for example ``C1_Count``).
    """

    if "_" not in column:
        return None
    tokens = column.split("_")
    if not tokens or tokens[0] not in FORM_ORDER:
        return None
    form = tokens[0]
    sensors_set = {sensor.strip() for sensor in sensors}
    sensor_index = None
    for idx in range(1, len(tokens)):
        token = tokens[idx].strip()
        if token in sensors_set:
            sensor_index = idx
            sensor = token
            break
    if sensor_index is None or sensor_index + 1 >= len(tokens):
        return None
    raw_title_tokens = tokens[1:sensor_index]
    if not raw_title_tokens:
        return None
    title = _normalise_title("_".join(raw_title_tokens))
    tail_tokens = tokens[sensor_index + 1 :]
    parsed_tail = _stat_from_tokens(tail_tokens, known_stats=known_stats)
    if not parsed_tail:
        return None
    stat, metric_tokens = parsed_tail
    metric = "_".join(metric_tokens)
    if not metric:
        return None
    return BiometricHeader(
        form=form,
        title=title,
        sensor=sensor,
        metric=metric,
        stat=stat,
        column=column,
    )


def _default_id_column(df: pd.DataFrame) -> str:
    """Return the best-effort respondent identifier column."""

    for candidate in ("respondent_id", "respondent", "RespondentID", "id"):
        if candidate in df.columns:
            return candidate
    return df.columns[0]


def reshape_biometric_long(
    df: pd.DataFrame,
    *,
    sensors: Sequence[str] | None = None,
    titles: Sequence[str] | None = None,
    stats: Sequence[str] | None = None,
    id_column: str | None = None,
    dropna: bool = True,
) -> pd.DataFrame:
    """Convert wide biometric UV data into a tidy long-form table.

    Parameters
    ----------
    df:
        Wide biometric dataframe (for example ``uv_biometric_full``).
    sensors:
        Optional iterable restricting sensors to include. Defaults to the four
        biometric sensors (EEG, ET, FAC, GSR).
    titles:
        Optional iterable of titles to retain. Comparisons are performed using
        canonical casing fixes so callers can pass corrected spellings.
    stats:
        Optional list of stat suffixes to keep.
    id_column:
        Column containing respondent identifiers. When ``None`` the helper will
        use ``respondent_id`` if available, falling back to the first column.
    dropna:
        Drop rows where the value cannot be coerced to a numeric type.
    """

    target_sensors = tuple(sensors) if sensors is not None else ("EEG", "ET", "FAC", "GSR")
    sensor_set = {sensor.strip() for sensor in target_sensors}
    id_col = id_column or _default_id_column(df)
    respondent_series = df[id_col].astype(str)
    title_set = None
    if titles is not None:
        title_set = {_normalise_title(title).lower() for title in titles}
    stats_set = None
    if stats is not None:
        stats_set = {stat for stat in stats}

    frames: list[pd.DataFrame] = []
    for column in df.columns:
        header = parse_biometric_header(column)
        if not header:
            continue
        if header.sensor not in sensor_set:
            continue
        if title_set is not None and header.title.lower() not in title_set:
            continue
        if stats_set is not None and header.stat not in stats_set:
            continue
        values = pd.to_numeric(df[column], errors="coerce")
        frame = pd.DataFrame(
            {
                "respondent_id": respondent_series,
                "form": header.form,
                "title": header.title,
                "sensor": header.sensor,
                "metric": header.metric,
                "stat": header.stat,
                "value": values,
            }
        )
        if dropna:
            frame = frame.dropna(subset=["value"])
        frames.append(frame)

    if not frames:
        return pd.DataFrame(
            columns=[
                "respondent_id",
                "form",
                "title",
                "sensor",
                "metric",
                "stat",
                "value",
            ]
        )

    long_df = pd.concat(frames, ignore_index=True)
    long_df["form"] = pd.Categorical(long_df["form"], categories=FORM_ORDER, ordered=True)
    return long_df


def summarise_biometric_structure(
    long_df: pd.DataFrame,
    *,
    id_column: str = "respondent_id",
) -> pd.DataFrame:
    """Return record counts and respondent coverage by sensor/metric/stat."""

    if long_df.empty:
        return pd.DataFrame(columns=["sensor", "metric", "stat", "form", "records", "respondents"])
    grouped = (
        long_df
        .groupby(["sensor", "metric", "stat", "form"], observed=True)
        .agg(
            records=("value", "count"),
            respondents=(id_column, "nunique"),
        )
        .reset_index()
    )
    return grouped


def _matching_duration_column(columns: Iterable[str], form: str, title: str) -> str | None:
    """Locate the duration column for a given title regardless of spelling."""

    candidates = []
    canon = _normalise_title(title)
    variants = {canon}
    for key, value in TITLE_FIXES.items():
        if value == canon:
            variants.add(value)
            variants.add(key.title())
            variants.add(key)
    for variant in variants:
        candidates.append(f"{form}_{variant}_duration")
    lower_lookup = {col.lower(): col for col in columns}
    for candidate in candidates:
        match = lower_lookup.get(candidate.lower())
        if match:
            return match
    return None


def get_duration_differences(
    df: pd.DataFrame,
    titles: Sequence[str],
    *,
    forms: Sequence[str] = FORM_ORDER,
) -> pd.DataFrame:
    """Compute duration deltas between Long and Short formats per title."""

    if "Long" not in forms or "Short" not in forms:
        raise ValueError("Duration comparison requires both 'Long' and 'Short' forms.")

    records: list[dict[str, float | str]] = []
    for title in titles:
        long_col = _matching_duration_column(df.columns, "Long", title)
        short_col = _matching_duration_column(df.columns, "Short", title)
        if not long_col or not short_col:
            continue
        long_vals = pd.to_numeric(df[long_col], errors="coerce")
        short_vals = pd.to_numeric(df[short_col], errors="coerce")
        delta = short_vals - long_vals
        valid_delta = delta.dropna()
        long_mean = float(long_vals.mean()) if not long_vals.empty else np.nan
        short_mean = float(short_vals.mean()) if not short_vals.empty else np.nan
        mean_diff = (
            float(short_mean - long_mean)
            if np.isfinite(long_mean) and np.isfinite(short_mean)
            else np.nan
        )
        stats = {
            "title": _normalise_title(title),
            "long_column": long_col,
            "short_column": short_col,
            "n": int(valid_delta.count()),
            "paired_mean_diff": (
                float(valid_delta.mean()) if not valid_delta.empty else np.nan
            ),
            "paired_std_diff": (
                float(valid_delta.std(ddof=1))
                if valid_delta.size > 1
                else np.nan
            ),
            "paired_min_diff": (
                float(valid_delta.min()) if not valid_delta.empty else np.nan
            ),
            "paired_max_diff": (
                float(valid_delta.max()) if not valid_delta.empty else np.nan
            ),
            "long_mean": long_mean,
            "short_mean": short_mean,
            "mean_diff": mean_diff,
            "abs_mean_diff": (
                abs(mean_diff) if np.isfinite(mean_diff) else np.nan
            ),
        }
        records.append(stats)
    return pd.DataFrame(records)


__all__ = [
    "BiometricHeader",
    "KNOWN_SENSORS",
    "KNOWN_STATS",
    "TITLE_FIXES",
    "FORM_ORDER",
    "get_duration_differences",
    "parse_biometric_header",
    "reshape_biometric_long",
    "summarise_biometric_structure",
]
