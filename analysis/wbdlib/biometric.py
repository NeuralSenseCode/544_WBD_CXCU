
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Literal, Mapping, Sequence

import numpy as np
import pandas as pd

from .stats import one_tailed_p_from_paired_t


def bin_biometric_time_series(
    long_df: pd.DataFrame,
    *,
    time_col: str = "time",
    value_col: str = "value",
    bin_width: float = 1.0,
    min_time: float | None = None,
    max_time: float | None = None,
    smoothing: Callable[[pd.Series], pd.Series] | None = None,
    groupby_cols: Sequence[str] = (
        "respondent_id", "form", "title", "sensor", "metric", "stat"
    ),
    bin_label: str = "time_bin",
) -> pd.DataFrame:
    """
    Bin and optionally smooth biometric time series in long-form DataFrame.

    Parameters
    ----------
    long_df : pd.DataFrame
        Long-form biometric data (from reshape_biometric_long), must include a
        time column.
    time_col : str
        Name of the time column (default: "time").
    value_col : str
        Name of the value column (default: "value").
    bin_width : float
        Width of each time bin (in seconds, default: 1.0).
    min_time : float or None
        Minimum time to include (default: min in data).
    max_time : float or None
        Maximum time to include (default: max in data).
    smoothing : Callable or None
        Optional smoothing function to apply to each binned series (e.g., moving
        average).
    groupby_cols : Sequence[str]
        Columns to group by before binning (default: respondent_id, form, title,
        sensor, metric, stat).
    bin_label : str
        Name of the output bin column (default: "time_bin").

    Returns
    -------
    pd.DataFrame
        DataFrame with binned (and optionally smoothed) values, preserving group
        columns and bin label.
    """
    df = long_df.copy()
    if time_col not in df.columns:
        raise ValueError(f"Time column '{time_col}' not found in DataFrame.")
    if value_col not in df.columns:
        raise ValueError(f"Value column '{value_col}' not found in DataFrame.")
    # Ensure time is float
    df[time_col] = pd.to_numeric(df[time_col], errors="coerce")
    df = df.dropna(subset=[time_col, value_col])
    # Set min/max time
    min_t = min_time if min_time is not None else df[time_col].min()
    max_t = max_time if max_time is not None else df[time_col].max()
    # Clip to range
    df = df[(df[time_col] >= min_t) & (df[time_col] <= max_t)]
    # Compute bin edges and assign bins
    bin_edges = np.arange(min_t, max_t + bin_width, bin_width)
    df[bin_label] = pd.cut(
        df[time_col], bins=bin_edges, right=False, labels=bin_edges[:-1]
    )
    # Convert bin label to float
    df[bin_label] = df[bin_label].astype(float)
    # Group and aggregate
    agg_cols = list(groupby_cols) + [bin_label]
    binned = (
        df.groupby(agg_cols, observed=True)[value_col]
        .mean()
        .reset_index()
    )
    # Optional smoothing per group
    if smoothing is not None:
        def _apply_smooth(subdf):
            subdf = subdf.sort_values(bin_label)
            subdf[value_col] = smoothing(subdf[value_col])
            return subdf
        binned = (
            binned.groupby(groupby_cols, group_keys=False, observed=True)
            .apply(_apply_smooth)
            .reset_index(drop=True)
        )

    return binned


# Biometric data helpers shared across notebooks.

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

OutlierMethod = Literal["iqr", "zscore"]
DEFAULT_OUTLIER_METHOD: OutlierMethod = "iqr"


def _iqr_bounds(
    series: pd.Series, *, whisker_width: float = 1.5
) -> tuple[float, float] | None:
    """Return Tukey IQR bounds for the provided series."""

    finite = series.dropna()
    if finite.empty:
        return None
    q1 = finite.quantile(0.25)
    q3 = finite.quantile(0.75)
    iqr = q3 - q1
    if not np.isfinite(iqr) or iqr == 0:
        return None
    lower = q1 - whisker_width * iqr
    upper = q3 + whisker_width * iqr
    return float(lower), float(upper)


def _z_scores(series: pd.Series) -> pd.Series | None:
    """Return z-scores for the provided series, or None if undefined."""

    finite = series.dropna()
    if finite.empty:
        return None
    std = finite.std(ddof=0)
    if not np.isfinite(std) or std == 0:
        return None
    mean = float(finite.mean())
    return (series - mean) / std


def _identify_outlier_rows(
    pivot: pd.DataFrame,
    *,
    method: OutlierMethod,
    whisker_width: float = 1.5,
    z_threshold: float = 3.0,
) -> pd.Series:
    """Return boolean mask covering respondents flagged as outliers."""

    if pivot.empty:
        return pd.Series(False, index=pivot.index, dtype=bool)

    mask = pd.Series(False, index=pivot.index, dtype=bool)
    value_columns = [col for col in ("Long", "Short") if col in pivot.columns]
    if not value_columns:
        return mask

    if method == "iqr":
        for column in value_columns:
            bounds = _iqr_bounds(pivot[column], whisker_width=whisker_width)
            if bounds is None:
                continue
            lower, upper = bounds
            mask = mask | (pivot[column] < lower) | (pivot[column] > upper)
        if set(value_columns) == {"Long", "Short"}:
            diff = pivot["Long"] - pivot["Short"]
            bounds = _iqr_bounds(diff, whisker_width=whisker_width)
            if bounds is not None:
                lower, upper = bounds
                mask = mask | (diff < lower) | (diff > upper)
    elif method == "zscore":
        for column in value_columns:
            z_scores = _z_scores(pivot[column])
            if z_scores is None:
                continue
            mask = mask | (z_scores.abs() > z_threshold)
        if set(value_columns) == {"Long", "Short"}:
            diff = pivot["Long"] - pivot["Short"]
            z_scores = _z_scores(diff)
            if z_scores is not None:
                mask = mask | (z_scores.abs() > z_threshold)
    else:
        raise ValueError(f"Unsupported outlier method '{method}'")

    return mask.fillna(False)


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


def canonicalise_title(text: str) -> str:
    """Public helper returning the canonical representation for a title."""

    if text is None:
        return ""
    return _normalise_title(str(text))


def _stat_from_tokens(
    tokens: Sequence[str],
    *,
    known_stats: Sequence[str],
) -> tuple[str, Sequence[str]] | None:
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
    """Parse a UV biometric column into its constituent components."""

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
    tail_tokens = tokens[sensor_index + 1:]
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

    for candidate in (
        "respondent_id",
        "respondent",
        "RespondentID",
        "id",
    ):
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
    """Convert wide biometric UV data into a tidy long-form table."""

    target_sensors = (
        tuple(sensors) if sensors is not None else ("EEG", "ET", "FAC", "GSR")
    )
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
    long_df["form"] = pd.Categorical(
        long_df["form"],
        categories=FORM_ORDER,
        ordered=True,
    )
    return long_df


@dataclass(frozen=True)
class WithinSubjectSummary:
    """Paired long-vs-short comparison outcome for one metric/stat."""

    metric: str
    stat: str
    long_mean: float
    short_mean: float
    difference: float
    p_value: float
    t_stat: float
    df: int
    n_pairs: int
    outliers_removed: int
    outlier_ids: tuple[object, ...]
    summary_row: Mapping[str, float | int | str]
    paired: pd.DataFrame


def compute_within_subject_summary(
    long_df: pd.DataFrame,
    metric: str,
    stat: str,
    *,
    id_column: str = "respondent_id",
    outlier_method: OutlierMethod | None = DEFAULT_OUTLIER_METHOD,
) -> WithinSubjectSummary:
    """Return descriptive and inferential stats for a metric/stat pairing."""

    columns = [
        "Metric",
        "Stat",
        "Long mean",
        "Short mean",
        "Difference",
        "t statistic",
        "df",
        "p (one-tailed)",
        "n paired",
        "Outliers removed",
    ]
    empty_summary = {
        "Metric": metric,
        "Stat": stat,
        "Long mean": np.nan,
        "Short mean": np.nan,
        "Difference": np.nan,
        "t statistic": np.nan,
        "df": np.nan,
        "p (one-tailed)": np.nan,
        "n paired": 0,
        "Outliers removed": 0,
    }
    subset = long_df.loc[
        (long_df["metric"] == metric) & (long_df["stat"] == stat)
    ]
    if subset.empty:
        paired_empty = pd.DataFrame(columns=["Long", "Short"])
        return WithinSubjectSummary(
            metric=metric,
            stat=stat,
            long_mean=np.nan,
            short_mean=np.nan,
            difference=np.nan,
            p_value=np.nan,
            t_stat=np.nan,
            df=0,
            n_pairs=0,
            outliers_removed=0,
            outlier_ids=tuple(),
            summary_row=empty_summary,
            paired=paired_empty,
        )

    pivot = subset.pivot_table(
        index=id_column,
        columns="form",
        values="value",
        aggfunc="mean",
        observed=True,
    )
    if isinstance(pivot.columns, pd.MultiIndex):
        pivot.columns = pivot.columns.droplevel(0)
    outliers_removed = 0
    outlier_ids: tuple[object, ...] = tuple()
    if outlier_method is not None:
        outlier_mask = _identify_outlier_rows(
            pivot, method=outlier_method
        )
        outliers_removed = int(outlier_mask.sum())
        if outliers_removed:
            outlier_ids = tuple(pivot.index[outlier_mask])
            pivot = pivot.loc[~outlier_mask]
        else:
            outlier_ids = tuple()
    long_scores = (
        pivot["Long"]
        if "Long" in pivot.columns
        else pd.Series(dtype=float)
    )
    short_scores = (
        pivot["Short"]
        if "Short" in pivot.columns
        else pd.Series(dtype=float)
    )
    long_mean = float(long_scores.mean()) if not long_scores.empty else np.nan
    short_mean = (
        float(short_scores.mean()) if not short_scores.empty else np.nan
    )
    difference = (
        long_mean - short_mean
        if np.isfinite(long_mean) and np.isfinite(short_mean)
        else np.nan
    )
    paired = pd.DataFrame(columns=["Long", "Short"])
    p_value = np.nan
    t_statistic = np.nan
    df = 0
    n_pairs = 0
    try:
        t_statistic, df, p_one, paired = one_tailed_p_from_paired_t(
            long_scores,
            short_scores,
        )
        p_value = float(p_one)
        t_statistic = float(t_statistic)
        n_pairs = paired.shape[0]
    except ValueError:
        paired = pd.DataFrame(columns=["Long", "Short"])

    summary_row = {
        "Metric": metric,
        "Stat": stat,
        "Long mean": long_mean,
        "Short mean": short_mean,
        "Difference": difference,
        "t statistic": t_statistic,
        "df": df,
        "p (one-tailed)": p_value,
        "n paired": n_pairs,
        "Outliers removed": outliers_removed,
    }
    for column in columns:
        summary_row.setdefault(column, empty_summary[column])

    return WithinSubjectSummary(
        metric=metric,
        stat=stat,
        long_mean=long_mean,
        short_mean=short_mean,
        difference=difference,
        p_value=p_value,
        t_stat=t_statistic,
        df=df,
        n_pairs=n_pairs,
        outliers_removed=outliers_removed,
        outlier_ids=outlier_ids,
        summary_row=summary_row,
        paired=paired,
    )


def build_within_subject_table(
    long_df: pd.DataFrame,
    metric: str,
    *,
    stats: Sequence[str] | None = None,
    id_column: str = "respondent_id",
    outlier_method: OutlierMethod | None = DEFAULT_OUTLIER_METHOD,
) -> tuple[pd.DataFrame, dict[str, WithinSubjectSummary]]:
    """Aggregate Part 1 results for all stats tied to a metric."""

    subset = long_df.loc[long_df["metric"] == metric]
    if stats is None:
        stats = tuple(sorted(subset["stat"].unique()))
    summary_rows: list[Mapping[str, float | int | str]] = []
    details: dict[str, WithinSubjectSummary] = {}
    for stat_item in stats:
        result = compute_within_subject_summary(
            subset,
            metric,
            stat_item,
            id_column=id_column,
            outlier_method=outlier_method,
        )
        summary_rows.append(result.summary_row)
        details[stat_item] = result
    if summary_rows:
        summary_df = pd.DataFrame(summary_rows)
    else:
        summary_df = pd.DataFrame(
            columns=[
                "Metric",
                "Stat",
                "Long mean",
                "Short mean",
                "Difference",
                "t statistic",
                "df",
                "p (one-tailed)",
                "n paired",
                "Outliers removed",
            ]
        )
    return summary_df, details


def summarise_biometric_structure(
    long_df: pd.DataFrame,
    *,
    id_column: str = "respondent_id",
) -> pd.DataFrame:
    """Return record counts and respondent coverage by sensor/metric/stat."""

    if long_df.empty:
        return pd.DataFrame(
            columns=[
                "sensor",
                "metric",
                "stat",
                "form",
                "records",
                "respondents",
            ]
        )
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


def _matching_duration_column(
    columns: Iterable[str],
    form: str,
    title: str,
) -> str | None:
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
        raise ValueError(
            "Duration comparison requires both 'Long' and 'Short' forms."
        )

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
        short_mean = (
            float(short_vals.mean()) if not short_vals.empty else np.nan
        )
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
    "WithinSubjectSummary",
    "bin_biometric_time_series",
    "canonicalise_title",
    "build_within_subject_table",
    "compute_within_subject_summary",
    "get_duration_differences",
    "parse_biometric_header",
    "reshape_biometric_long",
    "summarise_biometric_structure",
]
