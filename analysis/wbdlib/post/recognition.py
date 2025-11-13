"""Shared helpers for post questionnaire recognition parsing."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Iterable

import numpy as np
import pandas as pd

from .io import PostFile, extract_question_code, merge_duplicate_columns

TITLE_NORMALIZATION = {
    "abbott elementary": "Abbot Elementary",
    "abbot elementary": "Abbot Elementary",
    "schitts creek": "Schittss Creek",
    "schittss creek": "Schittss Creek",
    "mad max fury road": "Mad Max",
    "mad max": "Mad Max",
}

YES_VALUES = {"yes", "y", "true", "1"}
NO_VALUES = {"no", "n", "false", "0"}
CONFIDENCE_PATTERN = re.compile(r"^\s*([0-9]+(?:\.[0-9]+)?)")
RECOGNITION_BINARY_MAX = 2.0
RECOGNITION_CONFIDENCE_MAX = 4.0
RECOGNITION_COMPOSITE_MAX = RECOGNITION_BINARY_MAX * RECOGNITION_CONFIDENCE_MAX
FORM_CATEGORY_KEYS = {"key", "seen"}
NON_FORM_CATEGORY_KEYS = {"unseen", "fake", "distractor", "distractor2"}
STAT_LABELS = {
    "count": "Count",
    "sum": "Sum",
    "mean": "Mean",
    "normalized_mean": "NormalizedMean",
}


@dataclass(frozen=True)
class RecognitionContext:
    """Cached lookups used while parsing recognition responses."""

    uv_stage1_lookup: dict[str, dict[str, Any]]
    respondent_exposures: dict[str, dict[str, set[str]]]
    group_title_form_lookup: dict[tuple[str, str], str]
    uv_columns: pd.Index
    project_root: Path | None = None


@dataclass(frozen=True)
class RecognitionResult:
    """Structured output from recognition feature parsing."""

    features: pd.DataFrame
    issues: pd.DataFrame
    records: pd.DataFrame
    composite_columns: list[str]
    raw_columns: list[str]
    respondent_post_paths: dict[str, str]
    excluded_group_mismatch: set[str]


def canonicalize_title(raw_title: Any) -> str:
    """Normalize title strings to align across data sources."""
    if pd.isna(raw_title):
        return ""
    cleaned = str(raw_title).strip()
    if not cleaned:
        return ""
    lookup_key = cleaned.lower()
    return TITLE_NORMALIZATION.get(lookup_key, cleaned)


def _build_stage1_lookup(uv_stage1: pd.DataFrame) -> dict[str, dict[str, Any]]:
    required = {"respondent", "group"}
    missing = required - set(uv_stage1.columns)
    if missing:
        raise KeyError(
            "uv_stage1 must contain respondent and group columns; "
            f"missing {sorted(missing)}"
        )
    stage1 = uv_stage1.copy()
    stage1["respondent"] = stage1["respondent"].astype(str).str.strip()
    stage1["group"] = stage1["group"].astype(str).str.strip().str.upper()
    stage1 = stage1.dropna(subset=["respondent"])
    stage1 = stage1.drop_duplicates("respondent", keep="last")
    stage1_dict = stage1.set_index("respondent").to_dict("index")
    return {
        str(key): {
            str(inner_key): inner_value
            for inner_key, inner_value in value.items()
        }
        for key, value in stage1_dict.items()
    }


def _build_exposure_lookup(
    stage1_lookup: dict[str, dict[str, str]]
) -> dict[str, dict[str, set[str]]]:
    exposures: dict[str, dict[str, set[str]]] = {}
    for respondent_id, info in stage1_lookup.items():
        long_title = canonicalize_title(info.get("Long Form", ""))
        short_title = canonicalize_title(info.get("Short Form", ""))
        form_map: dict[str, set[str]] = {}
        if long_title:
            form_map.setdefault("Long", set()).add(long_title)
        if short_title:
            form_map.setdefault("Short", set()).add(short_title)
        if form_map:
            exposures[str(respondent_id)] = form_map
    return exposures


def _build_group_title_form_lookup(
    stimulus_map: pd.DataFrame,
) -> dict[tuple[str, str], str]:
    if not {"group", "title", "form"}.issubset(stimulus_map.columns):
        raise KeyError(
            "stimulus_map must contain group, title, and form columns"
        )
    lookup: dict[tuple[str, str], str] = {}
    for row in stimulus_map.itertuples():
        group_letter = getattr(row, "group", "")
        title_value = getattr(row, "title", "")
        form_value = getattr(row, "form", "")
        if not group_letter or not title_value or not form_value:
            continue
        group_clean = str(group_letter)[-1].upper()
        lookup[(group_clean, canonicalize_title(title_value))] = (
            str(form_value).title()
        )
    return lookup


def build_recognition_context(
    uv_stage1: pd.DataFrame,
    uv_stage2: pd.DataFrame | None,
    stimulus_map: pd.DataFrame,
    project_root: Path | None = None,
) -> RecognitionContext:
    """Create the helper context required for recognition parsing."""
    stage1_lookup = _build_stage1_lookup(uv_stage1)
    exposures = _build_exposure_lookup(stage1_lookup)
    group_title_form_lookup = _build_group_title_form_lookup(stimulus_map)
    uv_columns = (
        pd.Index(uv_stage2.columns)
        if uv_stage2 is not None
        else pd.Index(uv_stage1.columns)
    )
    return RecognitionContext(
        uv_stage1_lookup=stage1_lookup,
        respondent_exposures=exposures,
        group_title_form_lookup=group_title_form_lookup,
        uv_columns=uv_columns,
        project_root=project_root,
    )


def parse_yes_no(value: Any) -> float:
    """Convert a yes/no style answer into 1.0, 0.0, or NaN."""
    if isinstance(value, pd.Series):
        non_null = value.dropna()
        if non_null.empty:
            return np.nan
        value = non_null.iloc[0]
    if pd.isna(value):
        return np.nan
    text = str(value).strip().lower()
    if not text:
        return np.nan
    if text in YES_VALUES:
        return 1.0
    if text in NO_VALUES:
        return 0.0
    return np.nan


def parse_confidence(value: Any) -> float:
    """Parse a free-form confidence response into a numeric scale."""
    if isinstance(value, pd.Series):
        non_null = value.dropna()
        if non_null.empty:
            return np.nan
        value = non_null.iloc[0]
    if pd.isna(value):
        return np.nan
    text = str(value).strip()
    if not text:
        return np.nan
    match = CONFIDENCE_PATTERN.match(text)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return np.nan
    try:
        return float(text)
    except ValueError:
        return np.nan


def resolve_form(
    respondent_id: str,
    group_letter: str,
    title: str,
    context: RecognitionContext,
) -> tuple[str, list[str]]:
    """Infer the Long/Short form for a post-questionnaire record."""
    notes: list[str] = []
    exposures = context.respondent_exposures.get(respondent_id, {})
    canonical = canonicalize_title(title)
    if canonical:
        if canonical in exposures.get("Long", set()):
            return "Long", notes
        if canonical in exposures.get("Short", set()):
            return "Short", notes
    group_clean = (group_letter or "").strip().upper()
    if canonical:
        mapped = context.group_title_form_lookup.get((group_clean, canonical))
        if mapped:
            notes.append("form_from_group_stimulus_map")
            return mapped, notes
        has_short = any(
            col.startswith(f"Short_{canonical}") for col in context.uv_columns
        )
        has_long = any(
            col.startswith(f"Long_{canonical}") for col in context.uv_columns
        )
        if has_short and not has_long:
            notes.append("form_inferred_short_from_uv")
            return "Short", notes
        if has_long and not has_short:
            notes.append("form_inferred_long_from_uv")
            return "Long", notes
        if has_short and has_long:
            notes.append("form_ambiguous_default_short")
            return "Short", notes
    notes.append("form_unresolved_default_short")
    return "Short", notes


def _relative_path(path: Path, project_root: Path | None) -> str:
    if project_root is None:
        return path.as_posix()
    try:
        return path.relative_to(project_root).as_posix()
    except ValueError:
        return path.as_posix()


def _load_post_file(post_file: PostFile) -> pd.DataFrame:
    df_raw = pd.read_csv(post_file.path, dtype=str)
    df_merged = merge_duplicate_columns(df_raw)
    rename_map = {}
    for column in df_merged.columns:
        q_code = extract_question_code(column)
        if q_code:
            rename_map[column] = q_code
    df_standard = df_merged.rename(columns=rename_map)
    respondent_col = next(
        (
            col
            for col in df_standard.columns
            if "participant number" in col.lower()
        ),
        None,
    )
    if respondent_col is None:
        raise KeyError(
            "Participant identifier column not found in "
            f"{post_file.path.name}"
        )
    df_standard["respondent"] = (
        df_standard[respondent_col].astype(str).str.strip()
    )
    df_standard["respondent"] = df_standard["respondent"].replace(
        {"": np.nan, "nan": np.nan}
    )
    df_standard["respondent"] = df_standard["respondent"].str.replace(
        r"\.0$",
        "",
        regex=True,
    )
    if "Timestamp" in df_standard.columns:
        df_standard["timestamp_iso"] = pd.to_datetime(
            df_standard["Timestamp"],
            errors="coerce",
        )
    else:
        df_standard["timestamp_iso"] = pd.NaT
    return df_standard


def _build_meta_lookup(post_map: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    working = post_map.copy()
    if "question_code" not in working.columns:
        working.insert(
            1,
            "question_code",
            working["question"].apply(extract_question_code),
        )
    else:
        working["question_code"] = working["question"].apply(
            extract_question_code
        )
    recognition_map = working.loc[
        working["subscale"].astype(str).str.lower() == "recognition"
    ].copy()
    recognition_map["question_code"] = (
        recognition_map["question_code"].astype(str).str.strip()
    )
    recognition_map = recognition_map.loc[
        recognition_map["question_code"].str.match(r"^\d+\.[12]$")
    ]
    group_columns = [
        column
        for column in recognition_map.columns
        if column.startswith("Group ")
    ]
    meta_lookup: dict[tuple[str, str, str], dict[str, str]] = {}
    for row in recognition_map.itertuples():
        q_code = getattr(row, "question_code")
        q_root, q_suffix = q_code.split(".")
        category = str(getattr(row, "category", "")).strip()
        accuracy = str(getattr(row, "accuracy", "")).strip().lower()
        for group_col in group_columns:
            group_letter = group_col.replace("Group ", "").strip().upper()
            title_value = canonicalize_title(getattr(row, group_col, ""))
            meta_lookup[(group_letter, q_root, q_suffix)] = {
                "title": title_value,
                "category": category,
                "accuracy": accuracy,
            }
    return recognition_map, meta_lookup


def build_recognition_features(
    post_files: Iterable[PostFile],
    post_map: pd.DataFrame,
    context: RecognitionContext,
) -> RecognitionResult:
    """Parse recognition responses into feature and issue tables."""
    recognition_map, meta_lookup = _build_meta_lookup(post_map)
    valid_codes = set(recognition_map["question_code"].unique())
    recognition_records: list[dict[str, object]] = []
    issue_records: list[dict[str, object]] = []
    respondent_post_paths: dict[str, str] = {}
    excluded_group_mismatch: set[str] = set()

    for post_file in post_files:
        df_standard = _load_post_file(post_file)
        fallback_group = post_file.group_letter or ""
        for _, row in df_standard.iterrows():
            respondent_id = row.get("respondent")
            if pd.isna(respondent_id):
                continue
            respondent_id = str(respondent_id).strip()
            if not respondent_id:
                continue
            stage1_info = context.uv_stage1_lookup.get(respondent_id, {})
            stage1_group = str(stage1_info.get("group", "")).strip().upper()
            post_group = fallback_group
            if stage1_group and post_group and stage1_group != post_group:
                if respondent_id not in excluded_group_mismatch:
                    issue_records.append(
                        {
                            "respondent": respondent_id,
                            "group": stage1_group,
                            "question_number": np.nan,
                            "title": "",
                            "issue": (
                                "post_group_mismatch_uv_"
                                f"{stage1_group}_file_{post_group}"
                            ),
                            "source_file": post_file.path.name,
                        }
                    )
                excluded_group_mismatch.add(respondent_id)
                continue
            group_letter = stage1_group or post_group
            if not group_letter:
                issue_records.append(
                    {
                        "respondent": respondent_id,
                        "group": "",
                        "question_number": np.nan,
                        "title": "",
                        "issue": "group_missing_in_stage1_and_filename",
                        "source_file": post_file.path.name,
                    }
                )
                continue
            if respondent_id not in respondent_post_paths:
                respondent_post_paths[respondent_id] = _relative_path(
                    post_file.path,
                    context.project_root,
                )
            for code in valid_codes:
                if code not in row:
                    continue
                q_root, q_suffix = code.split(".")
                meta = meta_lookup.get((group_letter, q_root, q_suffix))
                if not meta:
                    continue
                binary_value = row.get(f"{q_root}.1")
                confidence_value = row.get(f"{q_root}.2")
                yes_no = parse_yes_no(binary_value)
                confidence = parse_confidence(confidence_value)
                issues_here: list[str] = []
                if np.isnan(yes_no):
                    issues_here.append(
                        "binary_response_missing_or_unrecognized"
                    )
                accuracy = meta.get("accuracy", "")
                expected_yes = accuracy == "hit"
                base_score_raw = np.nan
                base_score = np.nan
                if not np.isnan(yes_no):
                    answered_yes = bool(yes_no)
                    base_score_raw = (
                        RECOGNITION_BINARY_MAX
                        if answered_yes == expected_yes
                        else 0.0
                    )
                    base_score = base_score_raw / RECOGNITION_BINARY_MAX
                if np.isnan(confidence):
                    issues_here.append("confidence_missing_or_unrecognized")
                composite_raw = np.nan
                composite = np.nan
                if not np.isnan(base_score_raw) and not np.isnan(confidence):
                    composite_raw = base_score_raw * confidence
                    composite = composite_raw / RECOGNITION_COMPOSITE_MAX
                form_value, form_notes = resolve_form(
                    respondent_id,
                    group_letter,
                    meta.get("title", ""),
                    context,
                )
                issues_here.extend(form_notes)
                question_int = int(float(q_root))
                title_segment = meta.get("title", "").strip() or (
                    f"Question {question_int}"
                )
                composite_name = (
                    f"{form_value}_{title_segment}_Post_"
                    f"RecognitionComposite_Q{question_int:02d}"
                )
                base_name = (
                    f"{form_value}_{title_segment}_Post_"
                    f"Recognition_Q{question_int}-1"
                )
                confidence_name = (
                    f"{form_value}_{title_segment}_Post_"
                    f"Recognition_Q{question_int}-2"
                )
                timestamp = row.get("timestamp_iso", pd.NaT)
                for metric_label, feature_name, feature_value in [
                    ("composite", composite_name, composite),
                    ("binary", base_name, base_score),
                    ("confidence", confidence_name, confidence),
                ]:
                    recognition_records.append(
                        {
                            "respondent": respondent_id,
                            "group": group_letter,
                            "question_number": question_int,
                            "title": meta.get("title", ""),
                            "category": meta.get("category", ""),
                            "accuracy": accuracy,
                            "form": form_value,
                            "metric": metric_label,
                            "column_name": feature_name,
                            "value": feature_value,
                            "timestamp": timestamp,
                        }
                    )
                for issue in issues_here:
                    issue_records.append(
                        {
                            "respondent": respondent_id,
                            "group": group_letter,
                            "question_number": question_int,
                            "title": meta.get("title", ""),
                            "issue": issue,
                            "source_file": post_file.path.name,
                        }
                    )

    recognition_df = pd.DataFrame(recognition_records)
    if recognition_df.empty:
        raise ValueError(
            "No recognition responses were parsed from post "
            "questionnaire files."
        )
    recognition_df = recognition_df.sort_values(
        ["respondent", "column_name", "timestamp"]
    )
    recognition_df = recognition_df.drop_duplicates(
        ["respondent", "column_name"],
        keep="last",
    )

    recognition_features = (
        recognition_df.pivot(
            index="respondent",
            columns="column_name",
            values="value",
        )
        .sort_index(axis=1)
        .reset_index()
    )
    recognition_features.columns.name = None

    composite_subset = recognition_df.loc[
        recognition_df["metric"] == "composite"
    ].copy()
    if not composite_subset.empty:
        composite_subset["category_lower"] = (
            composite_subset["category"].astype(str).str.strip().str.lower()
        )
        composite_subset = composite_subset.loc[
            composite_subset["category_lower"].replace("", np.nan).notna()
        ]
        composite_subset["title_clean"] = composite_subset["title"].map(
            canonicalize_title
        )
        form_subset = composite_subset.loc[
            composite_subset["category_lower"].isin(FORM_CATEGORY_KEYS)
        ].copy()
        if not form_subset.empty:

            def _match_form(row: pd.Series) -> str | None:
                exposures = context.respondent_exposures.get(
                    row["respondent"],
                    {},
                )
                for form_label, titles in exposures.items():
                    if row["title_clean"] in titles:
                        return form_label
                return None

            form_subset["aligned_form"] = [
                _match_form(row)
                for _, row in form_subset.iterrows()
            ]
            unmatched_mask = form_subset["aligned_form"].isna()
            if unmatched_mask.any():
                for row in form_subset.loc[
                    unmatched_mask,
                    [
                        "respondent",
                        "question_number",
                        "title",
                        "category_lower",
                    ],
                ].itertuples(index=False):
                    respondent_key = str(row.respondent)
                    question_value = row.question_number
                    numeric_value = pd.to_numeric(
                        question_value,
                        errors="coerce",
                    )
                    if pd.isna(numeric_value):
                        question_display = np.nan
                    else:
                        question_display = int(float(numeric_value))
                    issue_records.append(
                        {
                            "respondent": respondent_key,
                            "group": context.uv_stage1_lookup.get(
                                respondent_key, {}
                            ).get("group", ""),
                            "question_number": question_display,
                            "title": row.title,
                            "issue": "post_form_title_not_in_stage1_exposures",
                            "source_file": respondent_post_paths.get(
                                respondent_key, ""
                            ),
                        }
                    )
                form_subset = form_subset.loc[~unmatched_mask]
            if not form_subset.empty:
                form_agg = (
                    form_subset.groupby(
                        ["respondent", "aligned_form", "category_lower"]
                    )["value"]
                    .agg(count="count", sum="sum", mean="mean")
                    .reset_index()
                )
                if not form_agg.empty:
                    form_agg["normalized_mean"] = (
                        form_agg["mean"].astype(float).clip(0, 1)
                    )
                    form_long = form_agg.melt(
                        id_vars=[
                            "respondent",
                            "aligned_form",
                            "category_lower",
                        ],
                        value_vars=["count", "sum", "mean", "normalized_mean"],
                        var_name="statistic",
                        value_name="stat_value",
                    )
                    form_long["column_name"] = form_long.apply(
                        lambda r: (
                            f"{r['aligned_form']}_{r['category_lower']}"
                            "_Post_Recognition_"
                            f"{STAT_LABELS[r['statistic']]}"
                        ),
                        axis=1,
                    )
                    form_wide = form_long.pivot(
                        index="respondent",
                        columns="column_name",
                        values="stat_value",
                    ).reset_index()
                    form_wide.columns.name = None
                    recognition_features = recognition_features.merge(
                        form_wide,
                        on="respondent",
                        how="left",
                    )
        non_form_subset = composite_subset.loc[
            composite_subset["category_lower"].isin(NON_FORM_CATEGORY_KEYS)
        ].copy()
        if not non_form_subset.empty:
            non_form_agg = (
                non_form_subset.groupby(
                    ["respondent", "category_lower"]
                )["value"]
                .agg(count="count", sum="sum", mean="mean")
                .reset_index()
            )
            if not non_form_agg.empty:
                non_form_agg["normalized_mean"] = (
                    non_form_agg["mean"].astype(float).clip(0, 1)
                )
                non_form_long = non_form_agg.melt(
                    id_vars=["respondent", "category_lower"],
                    value_vars=["count", "sum", "mean", "normalized_mean"],
                    var_name="statistic",
                    value_name="stat_value",
                )
                non_form_long["column_name"] = non_form_long.apply(
                    lambda r: (
                        f"{r['category_lower']}_Post_Recognition_"
                        f"{STAT_LABELS[r['statistic']]}"
                    ),
                    axis=1,
                )
                non_form_wide = non_form_long.pivot(
                    index="respondent",
                    columns="column_name",
                    values="stat_value",
                ).reset_index()
                non_form_wide.columns.name = None
                recognition_features = recognition_features.merge(
                    non_form_wide,
                    on="respondent",
                    how="left",
                )

    if respondent_post_paths:
        post_path_df = (
            pd.Series(respondent_post_paths, name="post_survey_source_path")
            .to_frame()
            .reset_index()
            .rename(columns={"index": "respondent"})
        )
        recognition_features = recognition_features.merge(
            post_path_df,
            on="respondent",
            how="left",
        )

    feature_columns = [
        col for col in recognition_features.columns if col != "respondent"
    ]
    composite_columns = [
        col for col in feature_columns if "_Post_RecognitionComposite_" in col
    ]
    raw_columns = [
        col
        for col in feature_columns
        if "_Post_Recognition_" in col
        and "Composite" not in col
        and not col.endswith("source_path")
    ]

    issues_df = pd.DataFrame(issue_records)
    if not issues_df.empty:
        issues_df = issues_df.sort_values(
            ["respondent", "question_number", "issue"]
        )

    return RecognitionResult(
        features=recognition_features,
        issues=issues_df,
        records=recognition_df,
        composite_columns=composite_columns,
        raw_columns=raw_columns,
        respondent_post_paths=respondent_post_paths,
        excluded_group_mismatch=excluded_group_mismatch,
    )


__all__ = [
    "RecognitionContext",
    "RecognitionResult",
    "build_recognition_context",
    "build_recognition_features",
    "canonicalize_title",
    "parse_confidence",
    "parse_yes_no",
    "resolve_form",
]
