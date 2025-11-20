"""Plotting helpers for seaborn/matplotlib integration."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import patches

from wbdlib.constants import BOXPLOT_MEANPROPS

_ORIGINAL_SNS_BOXPLOT = getattr(
    sns.boxplot,
    "__copilot_original__",
    sns.boxplot,
)


def annotate_boxplot_means(
    ax,
    data: pd.DataFrame,
    x: str,
    y: str,
    hue: str | None = None,
    order: Iterable[str] | None = None,
    hue_order: Iterable[str] | None = None,
    fmt: str = "{:.1f}",
    text_padding: float = 0.03,
) -> None:
    """Annotate seaborn boxplots with mean value labels."""
    if data is None or data.empty:
        return
    if x not in data.columns or y not in data.columns:
        return
    x_levels = (
        list(order)
        if order is not None
        else list(dict.fromkeys(data[x].dropna()))
    )
    if hue is None:
        combinations: list[tuple[tuple[str, ...], float]] = []
        for x_level in x_levels:
            values = data.loc[data[x] == x_level, y].dropna()
            if values.empty:
                continue
            combinations.append(((x_level,), values.mean()))
    else:
        if hue not in data.columns:
            return
        h_levels = (
            list(hue_order)
            if hue_order is not None
            else list(dict.fromkeys(data[hue].dropna()))
        )
        combinations = []
        for x_level in x_levels:
            for h_level in h_levels:
                mask = (data[x] == x_level) & (data[hue] == h_level)
                values = data.loc[mask, y].dropna()
                if values.empty:
                    continue
                combinations.append(((x_level, h_level), values.mean()))
    if not combinations:
        return
    boxes = [
        artist
        for artist in ax.artists
        if isinstance(artist, patches.PathPatch)
    ]
    if len(boxes) != len(combinations):
        candidates = [
            child
            for child in ax.get_children()
            if isinstance(child, patches.PathPatch)
        ]
        boxes = (
            candidates[-len(combinations):]
            if len(candidates) >= len(combinations)
            else []
        )
    if len(boxes) != len(combinations):
        return
    y_min, y_max = ax.get_ylim()
    y_span = y_max - y_min if np.isfinite(y_max - y_min) else 0.0
    offset = y_span * text_padding if y_span else 0.05
    inv_transform = ax.transData.inverted()
    for box, (combo_key, mean_val) in zip(boxes, combinations):
        if not np.isfinite(mean_val):
            continue
        try:
            bbox = box.get_path().get_extents(box.get_transform())
            center_disp = (bbox.x0 + bbox.x1) / 2.0
            x_pos = inv_transform.transform((center_disp, bbox.y0))[0]
        except (ValueError, TypeError, RuntimeError):  # pragma: no cover
            primary_level = combo_key[0] if combo_key else None
            if isinstance(primary_level, str) and primary_level in x_levels:
                x_pos = x_levels.index(primary_level)
            else:
                x_pos = 0.0
        ax.text(
            x_pos,
            mean_val + offset,
            fmt.format(mean_val),
            ha="center",
            va="bottom",
            fontsize=9,
            color="#2f2f2f",
            fontweight="bold",
        )


def boxplot_with_means(
    *args: Any,
    annotate: bool = True,
    annotate_kwargs: Mapping[str, Any] | None = None,
    **kwargs: Any,
):
    """Wrapper around seaborn.boxplot that adds a mean marker and label."""
    data = kwargs.get("data")
    if data is None and args:
        data = args[0]
    x = kwargs.get("x")
    y = kwargs.get("y")
    hue = kwargs.get("hue")
    order = kwargs.get("order")
    hue_order = kwargs.get("hue_order")
    annotation = kwargs.pop("annotation", None)
    palette = kwargs.get("palette")
    color_sequence: list[str] | None = None
    if (
        palette is not None
        and hue is None
        and x is not None
        and isinstance(data, pd.DataFrame)
        and x in data.columns
    ):
        if isinstance(palette, Mapping):
            levels = (
                list(order)
                if order is not None
                else list(dict.fromkeys(data[x].dropna()))
            )
            if levels:
                fallback = next(iter(palette.values()), "#4c72b0")
                color_sequence = [
                    palette.get(level, fallback)
                    for level in levels
                ]
        elif isinstance(palette, (list, tuple)):
            color_sequence = list(palette)
        if color_sequence:
            # Remove palette kwarg to avoid seaborn hue warning
            kwargs.pop("palette", None)
    kwargs["showmeans"] = True
    if "meanprops" not in kwargs:
        kwargs["meanprops"] = BOXPLOT_MEANPROPS
    ax = _ORIGINAL_SNS_BOXPLOT(*args, **kwargs)
    target_ax = kwargs.get("ax", ax)
    if color_sequence:
        # Apply palette manually to keep colors consistent
        boxes = [
            artist
            for artist in target_ax.artists
            if isinstance(artist, patches.PathPatch)
        ]
        if len(boxes) < len(color_sequence):
            extra_boxes = [
                child
                for child in target_ax.get_children()
                if isinstance(child, patches.PathPatch)
            ]
            boxes = (
                extra_boxes[-len(color_sequence):]
                if len(extra_boxes) >= len(color_sequence)
                else boxes
            )
        for patch, color in zip(boxes, color_sequence):
            patch.set_facecolor(color)
            patch.set_edgecolor("#222")
    if annotate and data is not None and x is not None and y is not None:
        annotate_params = {
            "ax": target_ax,
            "data": data,
            "x": x,
            "y": y,
            "hue": hue,
            "order": order,
            "hue_order": hue_order,
            "fmt": "{:.1f}",
        }
        if annotate_kwargs:
            annotate_params.update(dict(annotate_kwargs))
        annotate_boxplot_means(**annotate_params)
    # Draw a box around the plot (all spines visible)
    for spine in ["top", "right", "bottom", "left"]:
        ax.spines[spine].set_visible(True)
        ax.spines[spine].set_color("#222")
        ax.spines[spine].set_linewidth(1.2)
    # Optionally print annotation below plot
    if annotation:
        ax.text(
            0.0,
            -0.22,
            annotation,
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=9,
        )
    target_ax.figure.subplots_adjust(bottom=0.25, right=0.95)
    return ax


def register_boxplot_with_means() -> None:
    """Patch seaborn.boxplot so it always includes mean markers/labels."""
    sns.boxplot = boxplot_with_means
    boxplot_with_means.__copilot_showmeans__ = True
    boxplot_with_means.__copilot_original__ = _ORIGINAL_SNS_BOXPLOT


def bargraph_with_errors(
    data: pd.DataFrame,
    x: str,
    y: str,
    ax=None,
    palette=None,
    capsize=6,
    alpha=0.85,
    ylabel=None,
    title=None,
    **kwargs,
) -> Any:
    """Bar graph of means with standard error bars."""
    import matplotlib.pyplot as plt
    from scipy.stats import sem
    # Enforce self-report style globally for this plot
    plt.rcParams['font.family'] = "Century Gothic"
    plt.rcParams['figure.figsize'] = [8, 4]
    plt.rcParams.update({'font.size': 10})

    if ax is None:
        ax = plt.subplots()[1]
    annotation = kwargs.pop("annotation", None)
    means = data.groupby(x, observed=True)[y].mean()
    errors = data.groupby(x, observed=True)[y].apply(sem)
    color_list = None
    if palette:
        color_list = [palette.get(f, "#888") for f in means.index]
    means.plot(
        kind="bar",
        yerr=errors,
        ax=ax,
        color=color_list,
        capsize=capsize,
        alpha=alpha,
    )
    ax.tick_params(axis="x", labelrotation=0)
    if ylabel:
        ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title)
    ax.set_xlabel(x.capitalize())
    for spine in ["top", "right", "bottom", "left"]:
        ax.spines[spine].set_visible(True)
        ax.spines[spine].set_color("#222")
        ax.spines[spine].set_linewidth(1.2)
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    # Annotate means above bars (optional, matches boxplot_with_means style)
    for idx, val in enumerate(means):
        if np.isfinite(val):
            ax.text(
                idx,
                val
                + errors.iloc[idx]
                + 0.02 * (ax.get_ylim()[1] - ax.get_ylim()[0]),
                f"{val:.2f}",
                ha="center",
                va="bottom",
                fontsize=9,
                color="#2f2f2f",
                fontweight="bold",
            )
    # Optionally print annotation below plot
    if annotation:
        ax.text(
            0.0,
            -0.22,
            annotation,
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=9,
        )
    ax.figure.subplots_adjust(bottom=0.25, right=0.95)
    plt.tight_layout()
    return ax


__all__ = [
    "annotate_boxplot_means",
    "boxplot_with_means",
    "register_boxplot_with_means",
    "bargraph_with_errors",
    "BOXPLOT_MEANPROPS",
]
