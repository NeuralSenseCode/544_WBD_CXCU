"""Statistical helper functions."""

from __future__ import annotations

import pandas as pd
from scipy import stats


def one_tailed_p_from_paired_t(
    long_values,
    short_values,
):
    """Return paired t statistic, df, one-tailed p-value, and paired frame."""
    paired = pd.DataFrame({
        "Long": long_values,
        "Short": short_values,
    }).dropna()
    if paired.empty:
        raise ValueError(
            "No respondents have both Long and Short scores available."
        )
    t_stat, _ = stats.ttest_rel(
        paired["Long"],
        paired["Short"],
        nan_policy="omit",
    )
    df = paired.shape[0] - 1
    p_one = stats.t.sf(t_stat, df)
    return t_stat, df, p_one, paired


__all__ = ["one_tailed_p_from_paired_t"]
