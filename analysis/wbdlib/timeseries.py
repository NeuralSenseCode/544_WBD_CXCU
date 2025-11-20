"""Time-series helpers used by the biometric notebooks."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Callable, Mapping, Sequence

import numpy as np
import pandas as pd
from scipy.signal import butter, filtfilt

from .imotions import read_imotions


DEFAULT_SENSOR_METRICS: Mapping[str, tuple[str, ...]] = {
    "FAC": (
        "Anger",
        "Contempt",
        "Disgust",
        "Fear",
        "Joy",
        "Sadness",
        "Surprise",
        "Engagement",
        "Sentimentality",
        "Confusion",
        "Neutral",
    ),
    "EEG": (
        "High Engagement",
        "Low Engagement",
        "Distraction",
        "Drowsy",
        "Workload Average",
        "Frontal Alpha Asymmetry",
    ),
    "GSR": ("Peak Detected",
            "Phasic Signal"),
    "ET": (
        "Blink Detected",
        "Fixation Dispersion",
        "Fixation Index",
        "Fixation Duration",
    ),
}


@dataclass(frozen=True)
class KeyMomentWindow:
    """Structured representation of short and long-form key moment windows."""

    title: str
    short_start: float | None
    short_end: float | None
    long_start: float | None
    long_end: float | None
    short_duration: float | None
    long_duration: float | None
    key_moment_duration: float | None
    lead_up: float | None
    after: float | None
    total: float | None


@dataclass(frozen=True)
class TimeSeriesProcessingConfig:
    """Processing parameters applied while binning biometric time series."""

    bin_width: float
    min_coverage: float = 0.0
    smoothing: Callable[[pd.Series], pd.Series] | None = None
    label: str | None = None


@dataclass(frozen=True)
class SensorProcessingResult:
    """Container for respondent-level time-series processing outputs."""

    binned: pd.DataFrame
    diagnostics: pd.DataFrame
    issues: tuple[str, ...]
    metadata: Mapping[str, str]


@lru_cache(maxsize=1)
def _get_canonicalise_title():
    """Return canonicalise_title without triggering circular imports."""

    from .biometric import canonicalise_title

    return canonicalise_title


def _clean_group(value: object | None) -> str:
    if value is None:
        raise ValueError("Group label is required")
    cleaned = str(value).strip()
    if not cleaned:
        raise ValueError("Group label is required")
    cleaned = cleaned.replace("Group", "", 1).strip()
    if not cleaned:
        raise ValueError("Group label is required")
    return cleaned.upper()


def _canonical_token(value: object | None) -> str:
    if value is None:
        return ""
    text = str(value).lower()
    return "".join(ch for ch in text if ch.isalnum())


def _to_seconds(value: object | None) -> float | np.nan:
    if value is None:
        return np.nan
    if isinstance(value, (int, float)) and np.isfinite(value):
        return float(value)
    text = str(value).strip()
    if not text or text.upper() == "N/A":
        return np.nan
    try:
        delta = pd.to_timedelta(text)
    except (ValueError, TypeError):
        return np.nan
    if pd.isna(delta):
        return np.nan
    return float(delta.total_seconds())


def parse_duration_to_milliseconds(value: object | None) -> int | None:
    """Return duration expressed in milliseconds, or None when missing."""

    seconds = _to_seconds(value)
    if pd.isna(seconds):
        return None
    return int(round(float(seconds) * 1000.0))


def _maybe_float(value: object | None) -> float | None:
    if value is None:
        return None
    if isinstance(value, float) and np.isnan(value):
        return None
    if isinstance(value, pd.Series):
        if value.empty:
            return None
        value = value.iloc[0]
    return float(value)


def load_stimulus_map(path: str | Path) -> pd.DataFrame:
    """Return a cleaned stimulus rename table with canonical titles."""

    df = pd.read_csv(path)
    df.columns = [col.strip() for col in df.columns]
    required = {"group", "stimulus_name", "title", "form"}
    missing = required.difference(df.columns)
    if missing:
        missing_list = ", ".join(sorted(missing))
        raise KeyError(f"stimulus map missing columns: {missing_list}")
    df["group"] = df["group"].apply(_clean_group)
    df["stimulus_name"] = df["stimulus_name"].astype(str).str.strip()
    df["stimulus_key"] = df["stimulus_name"].map(_canonical_token)
    canonicalise = _get_canonicalise_title()
    df["title"] = df["title"].astype(str).map(canonicalise)
    df["form"] = df["form"].astype(str).str.strip().str.title()
    return df[["group", "stimulus_name", "stimulus_key", "title", "form"]]


def build_stimulus_lookup(
    stimulus_map: pd.DataFrame,
) -> dict[tuple[str, str], Mapping[str, str]]:
    """Return a lookup keyed by (group, canonical stimulus name)."""

    lookup: dict[tuple[str, str], Mapping[str, str]] = {}
    for row in stimulus_map.itertuples():
        key = (row.group, row.stimulus_key)
        record = {
            "stimulus_name": row.stimulus_name,
            "title": row.title,
            "form": row.form,
        }
        lookup[key] = record
    return lookup


def resolve_stimulus_identity(
    stimulus_name: str,
    group: str,
    stimulus_lookup: Mapping[tuple[str, str], Mapping[str, str]],
) -> tuple[str, str]:
    """Return the canonical (title, form) pair for a raw stimulus label."""

    group_key = _clean_group(group)
    stim_key = _canonical_token(stimulus_name)
    record = stimulus_lookup.get((group_key, stim_key))
    if record:
        return record["title"], record["form"]
    candidates = [
        record
        for (_group_key, token), record in stimulus_lookup.items()
        if token == stim_key
    ]
    if len(candidates) == 1:
        return candidates[0]["title"], candidates[0]["form"]
    raise KeyError(
        f"Could not resolve stimulus '{stimulus_name}' for group '{group_key}'"
    )


_TIME_COLUMNS: Mapping[str, str] = {
    "short_start": "Key moment start_OP",
    "short_duration": "Key moment Duration_OP",
    "short_end": "Key moment end_OP",
    "long_start": "Longform Start Time",
    "lead_up": "Lead-up Duration",
    "key_moment_duration": "Key moment Duration_LF",
    "long_end": "Longform End Time",
    "after": "After Key Moment  Duration",
    "total": "Total Duration",
}


def load_key_moments(path: str | Path) -> pd.DataFrame:
    """Load key moment definitions with durations expressed in seconds."""

    df = pd.read_csv(path)
    df.columns = [col.strip() for col in df.columns]
    if "title" not in df.columns:
        raise KeyError("key moment table missing 'title' column")
    canonicalise = _get_canonicalise_title()
    df["title"] = df["title"].astype(str).map(canonicalise)
    for column_name, source in _TIME_COLUMNS.items():
        if source in df.columns:
            df[column_name] = df[source].apply(_to_seconds)
        else:
            df[column_name] = np.nan
    if "long_duration" not in df.columns:
        df["long_duration"] = np.nan
    df["short_duration"] = df["short_duration"].fillna(
        df["short_end"] - df["short_start"]
    )
    df["long_duration"] = df["long_duration"].fillna(
        df["long_end"] - df["long_start"]
    )
    columns = [
        "title",
        *_TIME_COLUMNS.keys(),
        "short_duration",
        "long_duration",
    ]
    return df[columns]


def get_key_moment_window(
    title: str,
    key_moment_table: pd.DataFrame,
) -> KeyMomentWindow:
    """Return the key moment window information for a canonical title."""

    canonicalise = _get_canonicalise_title()
    canonical = canonicalise(title)
    subset = key_moment_table.loc[key_moment_table["title"] == canonical]
    if subset.empty:
        raise KeyError(f"No key moment entry for '{canonical}'")
    row = subset.iloc[0]
    return KeyMomentWindow(
        title=canonical,
        short_start=_maybe_float(row.get("short_start")),
        short_end=_maybe_float(row.get("short_end")),
        long_start=_maybe_float(row.get("long_start")),
        long_end=_maybe_float(row.get("long_end")),
        short_duration=_maybe_float(row.get("short_duration")),
        long_duration=_maybe_float(row.get("long_duration")),
        key_moment_duration=_maybe_float(row.get("key_moment_duration")),
        lead_up=_maybe_float(row.get("lead_up")),
        after=_maybe_float(row.get("after")),
        total=_maybe_float(row.get("total")),
    )


def load_sensor_file(
    path: str | Path,
    **read_csv_kwargs,
) -> tuple[pd.DataFrame, Mapping[str, str]]:
    """Load an iMotions sensor export and return data along with metadata."""

    frame, metadata = read_imotions(path, **read_csv_kwargs)
    if "Timestamp" in frame.columns:
        frame = frame.sort_values("Timestamp").reset_index(drop=True)
    return frame, metadata


def extract_stimulus_segment(
    frame: pd.DataFrame,
    stimulus_name: str,
    *,
    stimulus_col: str = "SourceStimuliName",
    timestamp_col: str = "Timestamp",
    event_col: str = "SlideEvent",
    start_label: str = "StartMedia",
    end_label: str = "EndMedia",
    align_to_zero: bool = True,
) -> pd.DataFrame:
    """Return the aligned time segment for a single stimulus."""

    if stimulus_col not in frame.columns:
        raise KeyError(f"Column '{stimulus_col}' not found in sensor frame")
    subset = frame.loc[frame[stimulus_col] == stimulus_name].copy()
    if subset.empty:
        raise KeyError(
            f"Stimulus '{stimulus_name}' not present in sensor file"
        )
    if timestamp_col not in subset.columns:
        raise KeyError(f"Column '{timestamp_col}' not found in sensor frame")
    start_series = subset.loc[subset[event_col] == start_label, timestamp_col]
    end_series = subset.loc[subset[event_col] == end_label, timestamp_col]
    start_value = (
        float(start_series.iloc[0])
        if not start_series.empty
        else float(subset[timestamp_col].min())
    )
    end_value = (
        float(end_series.iloc[-1])
        if not end_series.empty
        else float(subset[timestamp_col].max())
    )
    window = subset.loc[
        (subset[timestamp_col] >= start_value)
        & (subset[timestamp_col] <= end_value)
    ].copy()
    if align_to_zero:
        window["time_seconds"] = (window[timestamp_col] - start_value) / 1000.0
    return window


def bin_time_series(
    frame: pd.DataFrame,
    value_column: str,
    *,
    time_column: str = "time_seconds",
    bin_width: float,
    min_coverage: float | None = None,
) -> pd.DataFrame:
    """Aggregate a time-aligned series into fixed-width bins."""

    if bin_width <= 0:
        raise ValueError("bin_width must be positive")
    if time_column not in frame.columns:
        raise KeyError(f"Column '{time_column}' not present for binning")
    if value_column not in frame.columns:
        raise KeyError(f"Column '{value_column}' not present for binning")
    cleaned = frame[[time_column, value_column]].dropna()
    if cleaned.empty:
        return pd.DataFrame(
            columns=[
                "bin",
                "bin_start",
                "bin_end",
                "bin_midpoint",
                "value_mean",
                "value_median",
                "value_std",
                "sample_count",
                "coverage",
                "passes_coverage",
            ]
        )
    cleaned = cleaned.sort_values(time_column)
    bin_indices = np.floor(cleaned[time_column] / bin_width).astype(int)
    cleaned = cleaned.assign(bin=bin_indices)
    records: list[dict[str, float | int | bool]] = []
    for bin_id, chunk in cleaned.groupby("bin"):
        chunk = chunk.loc[(chunk[value_column] < 9000) &
                          (chunk[value_column] > -9000)]
        if chunk.empty:
            continue
        span = float(chunk[time_column].max() - chunk[time_column].min())
        effective_span = span
        if not np.isfinite(effective_span) or effective_span <= 0.0:
            diffs = (
                chunk[time_column]
                .sort_values()
                .diff()
                .dropna()
                .astype(float)
            )
            approx_spacing = (
                float(diffs.median()) if not diffs.empty else np.nan
            )
            if not np.isfinite(approx_spacing) or approx_spacing <= 0.0:
                approx_spacing = bin_width
            effective_span = approx_spacing
        coverage = min(1.0, effective_span / bin_width) if bin_width else 0.0
        passes = coverage >= (min_coverage or 0.0)
        values = chunk[value_column].astype(float)
        record = {
            "bin": int(bin_id),
            "bin_start": float(bin_id * bin_width),
            "bin_end": float((bin_id + 1) * bin_width),
            "bin_midpoint": float((bin_id + 0.5) * bin_width),
            "value_mean": float(values.mean()),
            "value_median": float(values.median()),
            "value_std": float(values.std(ddof=1)) if values.size > 1 else 0.0,
            "sample_count": int(values.size),
            "coverage": coverage,
            "passes_coverage": passes,
        }
        records.append(record)
    result = pd.DataFrame.from_records(records)
    result = result.sort_values("bin").reset_index(drop=True)
    return result


def _apply_zero_phase_filter(
    series: pd.Series,
    b: np.ndarray,
    a: np.ndarray,
) -> pd.Series:
    """Apply a filtfilt operation while preserving NaNs and index."""

    if series.empty:
        return series.astype(float)
    values = series.astype(float)
    mask = values.notna()
    if mask.sum() < max(len(a), len(b)) * 3:
        return values
    interpolated = values.interpolate(limit_direction="both")
    if interpolated.isna().any():
        interpolated = (
            interpolated.fillna(method="bfill").fillna(method="ffill")
        )
    if interpolated.isna().any():
        return values
    try:
        filtered = filtfilt(b, a, interpolated.to_numpy(), method="pad")
    except ValueError:
        return values
    result = pd.Series(filtered, index=series.index, name=series.name)
    result.loc[~mask] = np.nan
    return result


def butterworth_lowpass_filter(
    series: pd.Series,
    *,
    cutoff_hz: float,
    sample_rate_hz: float,
    order: int = 2,
) -> pd.Series:
    """Apply a low-pass Butterworth filter mirroring the AdNeuro pipeline."""

    if cutoff_hz <= 0 or sample_rate_hz <= 0:
        raise ValueError("cutoff_hz and sample_rate_hz must be positive")
    b, a = butter(
        order,
        cutoff_hz,
        fs=sample_rate_hz,
        btype="low",
        analog=False,
    )
    return _apply_zero_phase_filter(series, b, a)


def butterworth_highpass_filter(
    series: pd.Series,
    *,
    cutoff_hz: float,
    sample_rate_hz: float,
    order: int = 2,
) -> pd.Series:
    """Apply a high-pass Butterworth filter preserving original indexing."""

    if cutoff_hz <= 0 or sample_rate_hz <= 0:
        raise ValueError("cutoff_hz and sample_rate_hz must be positive")
    b, a = butter(
        order,
        cutoff_hz,
        fs=sample_rate_hz,
        btype="high",
        analog=False,
    )
    return _apply_zero_phase_filter(series, b, a)


def butterworth_bandpass_filter(
    series: pd.Series,
    *,
    low_cutoff_hz: float,
    high_cutoff_hz: float,
    sample_rate_hz: float,
    order: int = 2,
) -> pd.Series:
    """Apply a band-pass Butterworth filter with zero-phase response."""

    if low_cutoff_hz <= 0 or high_cutoff_hz <= 0:
        raise ValueError("Cutoff frequencies must be positive")
    if high_cutoff_hz <= low_cutoff_hz:
        raise ValueError("high_cutoff_hz must exceed low_cutoff_hz")
    if sample_rate_hz <= 0:
        raise ValueError("sample_rate_hz must be positive")
    b, a = butter(
        order,
        (low_cutoff_hz, high_cutoff_hz),
        fs=sample_rate_hz,
        btype="band",
        analog=False,
    )
    return _apply_zero_phase_filter(series, b, a)


def moving_average(
    series: pd.Series,
    window: int,
    *,
    center: bool = True,
    min_periods: int | None = None,
) -> pd.Series:
    """Return a rolling mean with defaults aligned to legacy notebooks."""

    if window <= 0:
        raise ValueError("window must be positive")
    min_count = 1 if min_periods is None else min_periods
    return (
        series.astype(float)
        .rolling(window=window, center=center, min_periods=min_count)
        .mean()
    )


def zscore_series(series: pd.Series) -> pd.Series:
    """Standardise a series to zero mean and unit variance."""

    values = series.astype(float)
    clean = values.dropna()
    if clean.empty:
        return pd.Series(np.nan, index=series.index, name=series.name)
    std = clean.std(ddof=0)
    if not np.isfinite(std) or std == 0:
        return pd.Series(np.nan, index=series.index, name=series.name)
    mean = float(clean.mean())
    return (values - mean) / std


def _create_moving_average_smoother(
    window: int,
) -> Callable[[pd.Series], pd.Series]:
    """Return a centred moving-average smoother with sensible defaults."""

    if window <= 0:
        raise ValueError("window must be positive")

    def _smooth(series: pd.Series) -> pd.Series:
        return moving_average(
            series,
            window=window,
            center=True,
            min_periods=1,
        )

    _smooth.__name__ = f"moving_average_{window}"
    return _smooth


def _create_lowpass_smoother(
    bin_width: float,
    *,
    cutoff_hz: float = 0.06,
    order: int = 2,
) -> Callable[[pd.Series], pd.Series]:
    """Return a Butterworth low-pass smoother parameterised by bin width."""

    if bin_width <= 0:
        raise ValueError("bin_width must be positive for smoothing")
    sample_rate = 1.0 / bin_width

    def _smooth(series: pd.Series) -> pd.Series:
        return butterworth_lowpass_filter(
            series,
            cutoff_hz=cutoff_hz,
            sample_rate_hz=sample_rate,
            order=order,
        )

    _smooth.__name__ = f"butterworth_lowpass_{cutoff_hz:.2f}Hz"
    return _smooth


def default_metric_columns() -> dict[str, tuple[str, ...]]:
    """Return a copy of the default sensor-to-metric mapping."""

    return {
        sensor: tuple(metrics)
        for sensor, metrics in DEFAULT_SENSOR_METRICS.items()
    }


def default_time_series_processing_config() -> dict[
    tuple[str, str],
    TimeSeriesProcessingConfig,
]:
    """Return the default per-metric processing configuration."""

    config: dict[tuple[str, str], TimeSeriesProcessingConfig] = {}
    for sensor, metrics in DEFAULT_SENSOR_METRICS.items():
        for metric in metrics:
            is_eeg_metric = (
                sensor == "EEG" and metric == "Frontal Asymmetry Alpha"
            )
            bin_width = 0.5 if is_eeg_metric else 1.0
            smoothing: Callable[[pd.Series], pd.Series] | None = None
            label: str | None = None
            if sensor == "EEG":
                if metric == "Workload Average":
                    smoothing = _create_lowpass_smoother(
                        bin_width,
                        cutoff_hz=0.06,
                        order=2,
                    )
                    label = "butterworth_lowpass_0.06Hz"
                else:
                    smoothing = _create_moving_average_smoother(window=3)
                    label = "moving_average_window3"
            config[(sensor, metric)] = TimeSeriesProcessingConfig(
                bin_width=bin_width,
                min_coverage=0.5,
                smoothing=smoothing,
                label=label,
            )
    return config


def _resolve_title_form_with_fallback(
    stimulus_name: str,
    group: object | None,
    stimulus_lookup: Mapping[tuple[str, str], Mapping[str, str]],
    stimulus_map: pd.DataFrame,
) -> tuple[str, str] | None:
    """Resolve raw stimulus to (title, form) even with missing group labels."""

    cleaned_group: str | None = None
    if group is not None:
        text = str(group).strip()
        if text:
            try:
                cleaned_group = _clean_group(text)
            except ValueError:
                cleaned_group = None
    if cleaned_group:
        try:
            return resolve_stimulus_identity(
                stimulus_name,
                cleaned_group,
                stimulus_lookup,
            )
        except KeyError:
            pass
    subset = stimulus_map.loc[stimulus_map["stimulus_name"] == stimulus_name]
    if subset.empty:
        return None
    if cleaned_group:
        matches = subset.loc[subset["group"] == cleaned_group]
        if not matches.empty:
            subset = matches
    row = subset.iloc[0]
    return row["title"], row["form"]


_BINNED_COLUMNS = [
    "respondent_id",
    "group",
    "title",
    "form",
    "sensor",
    "metric",
    "raw_stimulus",
    "bin_width",
    "smoothing_label",
    "bin",
    "bin_start",
    "bin_end",
    "bin_midpoint",
    "value_mean",
    "value_median",
    "value_std",
    "sample_count",
    "coverage",
    "passes_coverage",
    "value_smoothed",
]


_DIAGNOSTIC_COLUMNS = [
    "respondent_id",
    "group",
    "title",
    "form",
    "sensor",
    "metric",
    "raw_stimulus",
    "raw_samples",
    "bins_total",
    "bins_passing",
    "bins_failing",
    "mean_coverage",
    "max_time_seconds",
    "bin_width",
    "smoothing_label",
]


def _empty_binned_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=_BINNED_COLUMNS)


def _empty_diagnostic_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=_DIAGNOSTIC_COLUMNS)


_AGGREGATED_COLUMNS = [
    "group",
    "title",
    "form",
    "sensor",
    "metric",
    "bin_width",
    "smoothing_label",
    "bin",
    "bin_start",
    "bin_end",
    "bin_midpoint",
    "contributors",
    "total_samples",
    "mean_value",
    "median_value",
    "std_value",
    "sem_value",
    "ci95_low",
    "ci95_high",
    "mean_smoothed",
    "median_smoothed",
    "std_smoothed",
    "sem_smoothed",
    "ci95_low_smoothed",
    "ci95_high_smoothed",
    "mean_coverage",
]


def _empty_aggregated_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=_AGGREGATED_COLUMNS)


def aggregate_binned_time_series(
    binned: pd.DataFrame,
    *,
    min_contributors: int | None = None,
) -> pd.DataFrame:
    """Aggregate respondent-level bins into cohort-level summaries.

    Parameters
    ----------
    binned : pd.DataFrame
        Output from :func:`process_sensor_time_series` concatenated across
        respondents.
    min_contributors : int or None, optional
        If provided, drop aggregated bins contributed by fewer respondents.

    Returns
    -------
    pd.DataFrame
        Cohort-level aggregates with contributor counts and uncertainty bands.
    """

    if binned.empty:
        return _empty_aggregated_frame()

    required_columns = {
        "respondent_id",
        "group",
        "title",
        "form",
        "sensor",
        "metric",
        "smoothing_label",
        "bin",
        "bin_start",
        "bin_end",
        "bin_midpoint",
        "bin_width",
        "value_mean",
        "value_smoothed",
        "sample_count",
        "coverage",
        "passes_coverage",
    }
    missing = required_columns.difference(binned.columns)
    if missing:
        missing_list = ", ".join(sorted(missing))
        raise KeyError(
            f"binned frame missing required columns: {missing_list}"
        )

    filtered = binned.loc[binned["passes_coverage"].astype(bool)].copy()
    if filtered.empty:
        return _empty_aggregated_frame()

    group_fields = [
        "group",
        "title",
        "form",
        "sensor",
        "metric",
        "bin",
        "bin_start",
        "bin_end",
        "bin_midpoint",
        "bin_width",
        "smoothing_label",
    ]

    aggregated = (
        filtered.groupby(group_fields, dropna=False)
        .agg(
            contributors=("respondent_id", pd.Series.nunique),
            total_samples=("sample_count", "sum"),
            mean_value=("value_mean", "mean"),
            median_value=("value_mean", "median"),
            std_value=("value_mean", "std"),
            mean_smoothed=("value_smoothed", "mean"),
            median_smoothed=("value_smoothed", "median"),
            std_smoothed=("value_smoothed", "std"),
            mean_coverage=("coverage", "mean"),
        )
        .reset_index()
    )

    if aggregated.empty:
        return _empty_aggregated_frame()

    aggregated["std_value"] = aggregated["std_value"].fillna(0.0)
    aggregated["std_smoothed"] = aggregated["std_smoothed"].fillna(0.0)
    contributors = aggregated["contributors"].clip(lower=1).astype(float)

    aggregated["sem_value"] = aggregated["std_value"] / np.sqrt(contributors)
    aggregated["sem_smoothed"] = (
        aggregated["std_smoothed"] / np.sqrt(contributors)
    )

    z_score = 1.96
    aggregated["ci95_low"] = aggregated["mean_value"] - (
        aggregated["sem_value"] * z_score
    )
    aggregated["ci95_high"] = aggregated["mean_value"] + (
        aggregated["sem_value"] * z_score
    )
    aggregated["ci95_low_smoothed"] = (
        aggregated["mean_smoothed"] - aggregated["sem_smoothed"] * z_score
    )
    aggregated["ci95_high_smoothed"] = (
        aggregated["mean_smoothed"] + aggregated["sem_smoothed"] * z_score
    )

    if min_contributors:
        aggregated = aggregated.loc[
            aggregated["contributors"] >= min_contributors
        ]
        if aggregated.empty:
            return _empty_aggregated_frame()

    aggregated = aggregated[_AGGREGATED_COLUMNS].sort_values(
        ["title", "form", "sensor", "metric", "bin"]
    )
    aggregated = aggregated.reset_index(drop=True)
    return aggregated


def process_sensor_time_series(
    sensor_path: str | Path,
    *,
    respondent_id: object,
    group: object | None,
    stimulus_lookup: Mapping[tuple[str, str], Mapping[str, str]],
    stimulus_map: pd.DataFrame,
    key_moment_table: pd.DataFrame,
    metric_columns: Mapping[str, Sequence[str]] | None = None,
    processing_config: Mapping[
        tuple[str, str],
        TimeSeriesProcessingConfig,
    ]
    | None = None,
    default_config: TimeSeriesProcessingConfig | None = None,
    **read_csv_kwargs,
) -> SensorProcessingResult:
    """Process a respondent sensor file into binned series and diagnostics."""

    metrics_by_sensor = (
        {
            sensor: tuple(columns)
            for sensor, columns in (
                metric_columns or DEFAULT_SENSOR_METRICS
            ).items()
        }
    )

    required_columns: set[str] = {
        "Timestamp",
        "SourceStimuliName",
        "SlideEvent",
    }
    for metric_names in metrics_by_sensor.values():
        required_columns.update(metric_names)

    def _usecols(name: str) -> bool:
        return name in required_columns

    frame, metadata = load_sensor_file(
        sensor_path,
        usecols=_usecols,
        **read_csv_kwargs,
    )
    config_map = processing_config or default_time_series_processing_config()
    fallback_config = default_config or TimeSeriesProcessingConfig(
        bin_width=1.0
    )

    respondent_label = str(respondent_id)

    if "SourceStimuliName" not in frame.columns:
        issue = (
            f"{respondent_label}: sensor frame missing "
            "'SourceStimuliName' column"
        )
        return SensorProcessingResult(
            binned=_empty_binned_frame(),
            diagnostics=_empty_diagnostic_frame(),
            issues=(issue,),
            metadata=metadata,
        )

    cleaned_group: str | None = None
    if group is not None:
        text = str(group).strip()
        if text:
            try:
                cleaned_group = _clean_group(text)
            except ValueError:
                cleaned_group = None

    binned_frames: list[pd.DataFrame] = []
    diagnostic_rows: list[dict[str, object]] = []
    issues: list[str] = []

    for raw_name in frame["SourceStimuliName"].dropna().unique():
        resolved = _resolve_title_form_with_fallback(
            raw_name,
            cleaned_group or group,
            stimulus_lookup,
            stimulus_map,
        )
        if resolved is None:
            issues.append(
                f"{respondent_label}: no stimulus mapping for '{raw_name}'"
            )
            continue
        title, form = resolved
        try:
            segment = extract_stimulus_segment(frame, raw_name)
        except KeyError as exc:
            issues.append(f"{respondent_label}: {exc}")
            continue
        if segment.empty:
            continue
        if form == "Long":
            try:
                window = get_key_moment_window(title, key_moment_table)
            except KeyError as exc:
                issues.append(f"{respondent_label}: {exc}")
                continue
            lead = window.lead_up
            duration = window.key_moment_duration or window.long_duration
            if lead is None or duration is None:
                issues.append(
                    f"{respondent_label}: missing key-moment durations "
                    f"for '{title}'"
                )
                continue
            start = lead
            end = lead + duration
            segment = segment.loc[
                (segment["time_seconds"] >= start)
                & (segment["time_seconds"] <= end)
            ].copy()
            if segment.empty:
                issues.append(
                    f"{respondent_label}: empty window for '{title}' "
                    "after clipping"
                )
                continue
            segment["time_seconds"] = segment["time_seconds"] - start

        for sensor_label, metrics in metrics_by_sensor.items():
            if not metrics:
                continue
            for metric_name in metrics:
                if metric_name not in segment.columns:
                    continue
                metric_frame = segment[["time_seconds", metric_name]].copy()
                # Coerce raw sensor values to numeric in case of stray strings
                metric_frame["time_seconds"] = pd.to_numeric(
                    metric_frame["time_seconds"], errors="coerce"
                )
                metric_frame[metric_name] = pd.to_numeric(
                    metric_frame[metric_name], errors="coerce"
                )
                metric_frame = metric_frame.dropna(
                    subset=["time_seconds", metric_name]
                )
                raw_samples = int(metric_frame.shape[0])
                diagnostic_record = {
                    "respondent_id": respondent_id,
                    "group": cleaned_group,
                    "title": title,
                    "form": form,
                    "sensor": sensor_label,
                    "metric": metric_name,
                    "raw_stimulus": raw_name,
                    "raw_samples": raw_samples,
                    "bin_width": np.nan,
                    "smoothing_label": None,
                }
                if raw_samples == 0:
                    diagnostic_record.update(
                        {
                            "bins_total": 0,
                            "bins_passing": 0,
                            "bins_failing": 0,
                            "mean_coverage": np.nan,
                            "max_time_seconds": np.nan,
                        }
                    )
                    diagnostic_rows.append(diagnostic_record)
                    continue

                metric_frame = metric_frame.rename(
                    columns={metric_name: "value"}
                )
                metric_frame = metric_frame.sort_values("time_seconds")

                config = config_map.get(
                    (sensor_label, metric_name),
                    fallback_config,
                )
                diagnostic_record["bin_width"] = config.bin_width
                smoothing_label = config.label
                if smoothing_label is None and config.smoothing is not None:
                    smoothing_label = getattr(
                        config.smoothing,
                        "__name__",
                        "smoothing",
                    )
                diagnostic_record["smoothing_label"] = smoothing_label

                binned = bin_time_series(
                    metric_frame,
                    value_column="value",
                    time_column="time_seconds",
                    bin_width=config.bin_width,
                    min_coverage=config.min_coverage,
                )
                if binned.empty:
                    diagnostic_record.update(
                        {
                            "bins_total": 0,
                            "bins_passing": 0,
                            "bins_failing": 0,
                            "mean_coverage": np.nan,
                            "max_time_seconds": float(
                                metric_frame["time_seconds"].max()
                            ),
                        }
                    )
                    diagnostic_rows.append(diagnostic_record)
                    continue

                if config.smoothing is not None:
                    binned["value_smoothed"] = config.smoothing(
                        binned["value_mean"]
                    )
                else:
                    binned["value_smoothed"] = binned["value_mean"]

                binned = binned.assign(
                    respondent_id=respondent_id,
                    group=cleaned_group,
                    title=title,
                    form=form,
                    sensor=sensor_label,
                    metric=metric_name,
                    raw_stimulus=raw_name,
                    bin_width=config.bin_width,
                    smoothing_label=smoothing_label,
                )
                binned_frames.append(binned[_BINNED_COLUMNS])

                bins_total = int(binned.shape[0])
                bins_passing = int(binned["passes_coverage"].sum())
                bins_failing = bins_total - bins_passing
                mean_coverage = (
                    float(binned["coverage"].mean())
                    if bins_total
                    else np.nan
                )
                max_time_seconds = float(metric_frame["time_seconds"].max())

                diagnostic_record.update(
                    {
                        "bins_total": bins_total,
                        "bins_passing": bins_passing,
                        "bins_failing": bins_failing,
                        "mean_coverage": mean_coverage,
                        "max_time_seconds": max_time_seconds,
                    }
                )
                diagnostic_rows.append(diagnostic_record)

    binned_df = (
        pd.concat(binned_frames, ignore_index=True)
        if binned_frames
        else _empty_binned_frame()
    )
    diagnostics_df = (
        pd.DataFrame(diagnostic_rows, columns=_DIAGNOSTIC_COLUMNS)
        if diagnostic_rows
        else _empty_diagnostic_frame()
    )

    return SensorProcessingResult(
        binned=binned_df,
        diagnostics=diagnostics_df,
        issues=tuple(issues),
        metadata=metadata,
    )


__all__ = [
    "DEFAULT_SENSOR_METRICS",
    "KeyMomentWindow",
    "load_stimulus_map",
    "build_stimulus_lookup",
    "resolve_stimulus_identity",
    "load_key_moments",
    "get_key_moment_window",
    "load_sensor_file",
    "extract_stimulus_segment",
    "bin_time_series",
    "TimeSeriesProcessingConfig",
    "SensorProcessingResult",
    "parse_duration_to_milliseconds",
    "butterworth_lowpass_filter",
    "butterworth_highpass_filter",
    "butterworth_bandpass_filter",
    "moving_average",
    "zscore_series",
    "default_metric_columns",
    "default_time_series_processing_config",
    "process_sensor_time_series",
    "aggregate_binned_time_series",
]
