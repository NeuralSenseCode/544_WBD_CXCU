"""Survey and demographic helpers shared across WBD notebooks."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd

from .imotions import read_imotions
from .uv import extract_group_letter

LIKERT_PATTERN = re.compile(r"^\s*(\d+)(?:\.\d+)?")
LIKERT_KEYWORDS: Sequence[tuple[str, float]] = (
    ("strongly disagree", 1.0),
    ("disagree", 2.0),
    ("neither agree nor disagree", 3.0),
    ("strongly agree", 5.0),
    ("agree", 4.0),
)
FAMILIARITY_KEY_PATTERNS: Sequence[tuple[float, Sequence[str]]] = (
    (0.0, ("never heard", "not familiar")),
    (1.0, ("heard of it, but never watched", "heard of it only")),
    (2.0, ("seen a clip", "seen clips", "seen part")),
    (3.0, ("watched it in full", "just once")),
    (4.0, ("watched multiple", "very familiar")),
)
LASTWATCHED_KEY_PATTERNS: Sequence[tuple[float, Sequence[str]]] = (
    (4.0, ("past week",)),
    (3.0, ("past month", "past 6 months", "past six months")),
    (2.0, ("past 3 months", "past three months")),
    (1.0, ("more than 3 months", "over 3 months")),
    (
        0.0,
        (
            "more than 6 months",
            "don't remember",
            "never watched this movie in full",
        ),
    ),
)
DEFAULT_TIMEZONE = "America/Chicago"


def clean_response(value: Any) -> str | float:
    """Return stripped survey response text or ``np.nan`` for blanks."""
    if pd.isna(value):
        return np.nan  # type: ignore[return-value]
    text = str(value).strip()
    if not text or text.upper() == "EMPTY FIELD":
        return np.nan  # type: ignore[return-value]
    return text


def parse_likert_value(value: Any) -> float:
    """Parse a Likert response into a numeric value where possible."""
    text = clean_response(value)
    if pd.isna(text):
        return np.nan
    match = LIKERT_PATTERN.match(str(text))
    if match:
        return float(match.group(1))
    lowered = str(text).lower()
    for keyword, score in LIKERT_KEYWORDS:
        if keyword in lowered:
            return score
    try:
        return float(text)
    except (TypeError, ValueError):
        return np.nan


def score_familiarity(value: Any) -> float:
    """Score familiarity responses on a 0-4 scale."""
    text = clean_response(value)
    if pd.isna(text):
        return np.nan
    match = LIKERT_PATTERN.match(str(text))
    if match:
        numeric = float(match.group(1))
        return float(np.clip(numeric - 1.0, 0.0, 4.0))
    lowered = str(text).lower()
    for score, patterns in FAMILIARITY_KEY_PATTERNS:
        if any(pattern in lowered for pattern in patterns):
            return score
    try:
        numeric = float(text)
        return float(np.clip(numeric - 1.0, 0.0, 4.0))
    except (TypeError, ValueError):
        return np.nan


def score_last_watched(value: Any) -> float:
    """Score recency responses on a 0-4 scale using keyword heuristics."""
    text = clean_response(value)
    if pd.isna(text):
        return np.nan
    match = LIKERT_PATTERN.match(str(text))
    if match:
        numeric = float(match.group(1))
        return float(np.clip(numeric - 1.0, 0.0, 4.0))
    lowered = str(text).lower()
    for score, patterns in LASTWATCHED_KEY_PATTERNS:
        if any(pattern in lowered for pattern in patterns):
            return score
    try:
        numeric = float(text)
        return float(np.clip(numeric - 1.0, 0.0, 4.0))
    except (TypeError, ValueError):
        return np.nan


def reverse_likert(value: Any) -> float:
    """Flip a 1-5 Likert score in-place, returning ``np.nan`` for blanks."""
    if pd.isna(value):
        return np.nan
    try:
        return 6.0 - float(value)
    except (TypeError, ValueError):
        return np.nan


def clip_zero_to_four(value: Any) -> float:
    """Clip numeric values to the inclusive [0, 4] interval."""
    if pd.isna(value):
        return np.nan
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return np.nan
    return float(np.clip(numeric, 0.0, 4.0))


def parse_gender(raw_gender: Any | None) -> str | None:
    """Normalise demographic gender labels to Male, Female, or Other."""
    if not raw_gender:
        return None
    gender_lower = str(raw_gender).strip().lower()
    if "female" in gender_lower:
        return "Female"
    if "male" in gender_lower:
        return "Male"
    if "other" in gender_lower:
        return "Other"
    return str(raw_gender).strip().title() or None


def derive_respondent_identifier(
    raw_name: Any | None,
    fallback: str,
) -> str:
    """Extract numeric respondent IDs.

    Falls back to a provided filename stem when digits are unavailable.
    """
    if raw_name is None:
        return fallback
    text = str(raw_name).strip()
    if not text:
        return fallback
    digits = re.search(r"\d+", text)
    if digits:
        return digits.group(0)
    return text


def parse_recording_timestamp(
    recording_value: Any | None,
    *,
    timezone: str = DEFAULT_TIMEZONE,
) -> tuple[str | None, str | None]:
    """Extract date and time strings from iMotions recording metadata."""
    if not recording_value:
        return None, None
    fragments = [
        fragment.strip()
        for fragment in str(recording_value).split(",")
        if fragment.strip()
    ]
    date_part = None
    time_part = None
    for fragment in fragments:
        lowered = fragment.lower()
        if lowered.startswith("date:"):
            date_part = fragment.split(":", 1)[1].strip()
        elif lowered.startswith("time:"):
            time_part = fragment.split(":", 1)[1].strip()
    if date_part and time_part:
        dt_string = f"{date_part} {time_part}"
        timestamp = pd.to_datetime(dt_string, utc=True, errors="coerce")
        if pd.isna(timestamp):
            timestamp = pd.to_datetime(dt_string, errors="coerce")
            if pd.notna(timestamp) and timestamp.tzinfo is None:
                try:
                    timestamp = timestamp.tz_localize(timezone)
                except (TypeError, ValueError):
                    # pragma: no cover - fallback path
                    timestamp = timestamp.tz_localize("UTC")
        if pd.notna(timestamp):
            if timestamp.tzinfo is None:
                timestamp = timestamp.tz_localize(timezone)
            else:
                timestamp = timestamp.tz_convert(timezone)
            return (
                timestamp.strftime("%m/%d/%Y"),
                timestamp.strftime("%H:%M:%S"),
            )
        return date_part, time_part
    if date_part:
        return date_part, None
    return None, None


def infer_group_letter(
    study_name: Any | None,
    respondent_group: Any | None,
    source_path: str | Path | None = None,
) -> str | None:
    """Infer the respondent group letter from study metadata or file paths."""
    candidates: Sequence[object | None] = (
        study_name,
        respondent_group,
        source_path,
    )
    for candidate in candidates:
        if candidate is None:
            continue
        letter = extract_group_letter(candidate)
        if letter:
            return letter
    return None


def build_group_short_long_map() -> pd.DataFrame:
    """Return the canonical mapping of groups to short and long-form titles."""
    data = [
        ("A", "Mad Max", "The Town"),
        ("B", "The Town", "Mad Max"),
        ("C", "The Town", "Abbot Elementary"),
        ("D", "Abbot Elementary", "The Town"),
        ("E", "Abbot Elementary", "Mad Max"),
        ("F", "Mad Max", "Abbot Elementary"),
    ]
    mapping = pd.DataFrame(data, columns=["group", "Short Form", "Long Form"])
    for column in ("Short Form", "Long Form"):
        mapping[column] = mapping[column].str.strip().str.rstrip(",")
    return mapping


def get_files(
    folder: str | Path,
    tags: Iterable[str] | None = None,
) -> list[str]:
    """List files within a folder while filtering by optional substrings."""
    folder_path = Path(folder)
    tag_list = list(tags or [])
    return [
        name
        for name in os.listdir(folder_path)
        if not name.startswith(".") and all(tag in name for tag in tag_list)
    ]


def get_biometric_data(
    in_folder: str | Path,
    results_folder: str | Path,
    *,
    respondents: Sequence[int] | None = None,
    cols_afdex: Sequence[str] | None = None,
    cols_eeg: Sequence[str] | None = None,
    window_lengths: Sequence[int] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Legacy biometric feature extractor retained for reference.

    The implementation mirrors the original notebook helper: it aggregates
    sensor features per stimulus and writes ``biometric_results.csv`` and
    ``errors_biometric.csv`` under ``results_folder``. Both DataFrames are
    returned so callers can bypass the on-disk outputs if desired.
    """

    in_path = Path(in_folder)
    out_path = Path(results_folder)
    out_path.mkdir(parents=True, exist_ok=True)

    respondent_list = list(respondents or [1, 2, 3])
    afdex_columns = list(
        cols_afdex
        or (
            "Anger",
            "Contempt",
            "Disgust",
            "Fear",
            "Joy",
            "Sadness",
            "Surprise",
            "Engagement",
            "Valence",
            "Sentimentality",
            "Confusion",
            "Neutral",
        )
    )
    eeg_columns = list(
        cols_eeg
        or (
            "High Engagement",
            "Low Engagement",
            "Distraction",
            "Drowsy",
            "Workload Average",
            "Frontal Asymmetry Alpha",
        )
    )
    _ = list(window_lengths or [3])  # Placeholder retained for compatibility

    sensor_files = get_files(in_path / "Sensors", tags=[".csv"])

    interactions: list[Mapping[str, object]] = []
    errors: list[Mapping[str, object]] = []

    for respondent in respondent_list:
        error_record: dict[str, object | None] = {
            "respondent": respondent,
            "FAC": None,
            "EEG": None,
            "GSR": None,
            "Blinks": None,
            "ET": None,
        }
        interaction: dict[str, object] = {"respondent": respondent}
        try:
            file_name = next(
                file
                for file in sensor_files
                if str(respondent) in file
            )
            df_sensor, _ = read_imotions(in_path / "Sensors" / file_name)

            for task in df_sensor["SourceStimuliName"].dropna().unique():
                df_task = df_sensor.loc[df_sensor["SourceStimuliName"] == task]
                window = task

                for column in afdex_columns:
                    try:
                        series = df_task[column].dropna()
                        prefix = f"sens_{window}_FAC_{column}"
                        interaction[f"{prefix}_mean"] = series.mean()
                        auc_data = df_task[["Timestamp", column]].dropna()
                        auc_value = float(
                            np.trapz(
                                auc_data[column],
                                x=auc_data["Timestamp"],
                            )
                        ) / 1000.0
                        interaction[f"{prefix}_AUC"] = auc_value
                        interaction[f"{prefix}_Binary"] = series.max() >= 50
                    except (KeyError, ValueError, TypeError):
                        # pragma: no cover - legacy fallback
                        error_record["FAC"] = "Missing"

                for column in eeg_columns:
                    try:
                        series = df_task[column].dropna()
                        filtered = series[series > -9000]
                        prefix = f"sens_{window}_EEG_{column}"
                        interaction[f"{prefix}_mean"] = filtered.mean()
                        mask_eeg = (
                            df_task[column].notna()
                            & (df_task[column] > -9000)
                        )
                        auc_data = df_task.loc[mask_eeg, ["Timestamp", column]]
                        auc_value = float(
                            np.trapz(
                                auc_data[column],
                                x=auc_data["Timestamp"],
                            )
                        ) / 1000.0
                        interaction[f"{prefix}_AUC"] = auc_value
                    except (KeyError, ValueError, TypeError):
                        # pragma: no cover - legacy fallback
                        error_record["EEG"] = "Missing"

                try:
                    gsr_data = df_task[["Timestamp", "Peak Detected"]].dropna()
                    mask = gsr_data["Peak Detected"] == 1
                    segments = (mask != mask.shift()).cumsum()
                    count_patches = (
                        gsr_data.loc[mask, "Peak Detected"]
                        .groupby(segments)
                        .ngroup()
                        .nunique()
                    )
                    interaction[f"sens_{window}_GSR_PeakDetected_Binary"] = (
                        1 if gsr_data["Peak Detected"].sum() > 0 else 0
                    )
                    interaction[
                        f"sens_{window}_GSR_Peaks_Count"
                    ] = count_patches
                except (KeyError, ValueError, TypeError, IndexError):
                    # pragma: no cover - legacy fallback
                    error_record["GSR"] = "Missing"

                try:
                    blink_data = df_task[
                        ["Timestamp", "Blink Detected"]
                    ].dropna()
                    mask = blink_data["Blink Detected"] == 1
                    segments = (mask != mask.shift()).cumsum()
                    count_patches = (
                        blink_data.loc[mask, "Blink Detected"]
                        .groupby(segments)
                        .ngroup()
                        .nunique()
                    )
                    interaction[
                        f"sens_{window}_ET_Blink_Count"
                    ] = count_patches
                    duration_minutes = (
                        df_task["Timestamp"].iloc[-1]
                        - df_task["Timestamp"].iloc[0]
                    ) / (1000.0 * 60.0)
                    if duration_minutes:
                        interaction[f"sens_{window}_ET_Blink_Rate"] = (
                            count_patches / duration_minutes
                        )
                except (KeyError, ValueError, TypeError, IndexError):
                    # pragma: no cover - legacy fallback
                    error_record["ET"] = "Missing"

            interactions.append(interaction)
            errors.append(error_record)
        except StopIteration:
            print(f"Could not find sensor data for respondent {respondent}")
        except (OSError, ValueError, TypeError) as exc:
            # pragma: no cover - legacy fallback
            print(f"Failed to process respondent {respondent}: {exc}")

    results_df = pd.DataFrame(interactions)
    errors_df = pd.DataFrame(errors)

    results_path = out_path / "biometric_results.csv"
    errors_path = out_path / "errors_biometric.csv"
    results_df.to_csv(results_path, index=False)
    errors_df.to_csv(errors_path, index=False)

    return results_df, errors_df


__all__ = [
    "LIKERT_PATTERN",
    "LIKERT_KEYWORDS",
    "FAMILIARITY_KEY_PATTERNS",
    "LASTWATCHED_KEY_PATTERNS",
    "DEFAULT_TIMEZONE",
    "build_group_short_long_map",
    "clean_response",
    "clip_zero_to_four",
    "derive_respondent_identifier",
    "get_biometric_data",
    "get_files",
    "infer_group_letter",
    "parse_gender",
    "parse_likert_value",
    "parse_recording_timestamp",
    "reverse_likert",
    "score_familiarity",
    "score_last_watched",
]
