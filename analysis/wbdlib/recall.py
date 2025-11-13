"""Helpers for assembling open-ended recall structures."""

from __future__ import annotations

import re
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd


def build_open_recall_structures(
    uv: pd.DataFrame,
    id_column: str,
    target_titles: Iterable[str],
    pattern: re.Pattern[str],
    label: str,
    target_ceiling_lookup: Mapping[tuple[str, str], float] | None = None,
    form_column_lookup: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Build normalized, raw, and target-scaled recall tables."""
    if id_column not in uv.columns:
        raise KeyError(f"Missing respondent identifier column: {id_column}")

    forms_map = dict(
        form_column_lookup
        or {
            "Short": "Short Form",
            "Long": "Long Form",
        }
    )
    forms = tuple(forms_map.keys())
    target_titles = tuple(target_titles)
    target_title_set = {title.strip() for title in target_titles if title}
    id_values = uv[id_column].astype(str)

    series_map: dict[tuple[str, str], pd.Series] = {}
    series_map_raw: dict[tuple[str, str], pd.Series] = {}
    series_map_target: dict[tuple[str, str], pd.Series] = {}
    stats: list[dict[str, Any]] = []

    for column in uv.columns:
        match = pattern.match(column)
        if not match:
            continue
        form, raw_title = match.groups()
        if form not in forms:
            continue
        title = raw_title.replace("_", " ").strip()
        series = pd.to_numeric(uv[column], errors="coerce").replace(
            [np.inf, -np.inf], np.nan
        )
        valid = series.dropna()
        if valid.empty:
            continue
        col_min = valid.min()
        col_max = valid.max()
        if not (np.isfinite(col_min) and np.isfinite(col_max)):
            continue
        if np.isclose(col_max, col_min):
            norm_series = pd.Series(np.nan, index=series.index)
        else:
            norm_series = (
                (series - col_min)
                / (col_max - col_min)
            ).clip(0.0, 1.0)
        series_map[(form, title)] = norm_series
        series_map_raw[(form, title)] = series
        if target_ceiling_lookup:
            target_max = target_ceiling_lookup.get((form, title))
            if (
                target_max is not None
                and np.isfinite(target_max)
                and target_max > 0
            ):
                target_series = (series / float(target_max)).clip(0.0, 1.0)
                series_map_target[(form, title)] = target_series
        stats.append(
            {
                "form": form,
                "title": title,
                "min": float(col_min),
                "max": float(col_max),
                "range": float(col_max - col_min),
                "respondents": int(valid.shape[0]),
            }
        )

    if not series_map:
        raise ValueError(
            "No open-ended recall columns matching the "
            f"{label} pattern were found in uv_merged.csv."
        )

    def _concat_frames(frames: list[pd.DataFrame]) -> pd.DataFrame:
        return (
            pd.concat(frames, ignore_index=True)
            if frames
            else pd.DataFrame(columns=[id_column, "form", "title", "value"])
        )

    long_frames: list[pd.DataFrame] = []
    raw_frames: list[pd.DataFrame] = []
    target_frames: list[pd.DataFrame] = []

    for (form, title), norm_series in series_map.items():
        raw_series = series_map_raw[(form, title)]
        frame_norm = pd.DataFrame(
            {
                id_column: id_values,
                "form": form,
                "title": title,
                "value": norm_series,
            }
        ).dropna(subset=["value"])
        if not frame_norm.empty:
            long_frames.append(frame_norm)
        frame_raw = pd.DataFrame(
            {
                id_column: id_values,
                "form": form,
                "title": title,
                "value": raw_series,
            }
        ).dropna(subset=["value"])
        if not frame_raw.empty:
            raw_frames.append(frame_raw)
        target_series = series_map_target.get((form, title))
        if target_series is not None:
            frame_target = pd.DataFrame(
                {
                    id_column: id_values,
                    "form": form,
                    "title": title,
                    "value": target_series,
                }
            ).dropna(subset=["value"])
            if not frame_target.empty:
                target_frames.append(frame_target)

    open_long = _concat_frames(long_frames)
    open_long_raw = _concat_frames(raw_frames)
    open_long_target = _concat_frames(target_frames)

    def _set_form_categories(frame: pd.DataFrame) -> pd.DataFrame:
        if frame.empty:
            return frame
        result = frame.copy()
        result["form"] = pd.Categorical(
            result["form"],
            categories=list(forms),
            ordered=True,
        )
        return result

    if target_title_set:
        def _filter_targets(frame: pd.DataFrame) -> pd.DataFrame:
            if frame.empty:
                return frame
            filtered = frame.loc[frame["title"].isin(target_title_set)].copy()
            return _set_form_categories(filtered)

        open_long = _filter_targets(open_long)
        open_long_raw = _filter_targets(open_long_raw)
        open_long_target = _filter_targets(open_long_target)
    else:
        open_long = _set_form_categories(open_long)
        open_long_raw = _set_form_categories(open_long_raw)
        open_long_target = _set_form_categories(open_long_target)

    required_columns = [col for col in forms_map.values()]
    missing_columns = [
        col for col in required_columns if col not in uv.columns
    ]
    if missing_columns:
        raise KeyError(
            "Missing required UV columns for recall pairing: "
            f"{missing_columns}"
        )
    pairs = uv[required_columns].copy()
    pairs[id_column] = id_values
    for name in [
        "Short",
        "Long",
        "Short_raw",
        "Long_raw",
        "Short_target",
        "Long_target",
    ]:
        pairs[name] = np.nan

    for (form, title), norm_series in series_map.items():
        raw_series = series_map_raw[(form, title)]
        form_column = forms_map.get(form)
        if form_column is None:
            continue
        aligned_norm = norm_series.reindex(pairs.index)
        aligned_raw = raw_series.reindex(pairs.index)
        mask = pairs[form_column].astype(str).str.strip().eq(title)
        if not mask.any():
            continue
        pairs.loc[mask, form] = aligned_norm.loc[mask]
        raw_col = f"{form}_raw"
        pairs.loc[mask, raw_col] = aligned_raw.loc[mask]
        target_series = series_map_target.get((form, title))
        if target_series is not None:
            aligned_target = target_series.reindex(pairs.index)
            target_col = f"{form}_target"
            pairs.loc[mask, target_col] = aligned_target.loc[mask]

    stats_df = (
        pd.DataFrame(stats).sort_values([
            "form",
            "title",
        ], ignore_index=True)
        if stats
        else pd.DataFrame(
            columns=[
                "form",
                "title",
                "min",
                "max",
                "range",
                "respondents",
            ]
        )
    )

    return {
        "series_map": series_map,
        "series_map_raw": series_map_raw,
        "series_map_target": series_map_target,
        "long": open_long,
        "long_raw": open_long_raw,
        "long_target": open_long_target,
        "pairs": pairs,
        "stats": stats_df,
    }


__all__ = ["build_open_recall_structures"]
