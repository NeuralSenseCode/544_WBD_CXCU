"""Column categorisation helpers."""

from __future__ import annotations

from collections.abc import Iterable

DEMOGRAPHIC_EXACT: set[str] = {
    "respondent_id",
    "group",
    "age",
    "age_group",
    "gender",
    "ethnicity",
    "income_group",
    "content_consumption",
    "grid_comments",
    "date_study",
    "time_study",
    "post_survey_source_path",
}

DEMOGRAPHIC_KEYWORDS: tuple[str, ...] = (
    "demographic",
    "respondent",
    "grid",
    "age",
    "gender",
    "ethnic",
    "income",
    "content_consumption",
    "comments",
    "group",
)

ENJOYMENT_KEYWORDS: tuple[str, ...] = ("enjoy",)
FAMILIARITY_KEYWORDS: tuple[str, ...] = ("familiar",)
RECOGNITION_KEYWORDS: tuple[str, ...] = ("recognition", "recall")


def assign_category(
    column_name: str,
    demographic_exact: Iterable[str] | None = None,
    demographic_keywords: Iterable[str] | None = None,
    enjoyment_keywords: Iterable[str] | None = None,
    familiarity_keywords: Iterable[str] | None = None,
    recognition_keywords: Iterable[str] | None = None,
) -> str:
    """Return a coarse category label for a UV column header."""
    demographic_exact = set(demographic_exact or DEMOGRAPHIC_EXACT)
    demographic_keywords = tuple(demographic_keywords or DEMOGRAPHIC_KEYWORDS)
    enjoyment_keywords = tuple(enjoyment_keywords or ENJOYMENT_KEYWORDS)
    familiarity_keywords = tuple(familiarity_keywords or FAMILIARITY_KEYWORDS)
    recognition_keywords = tuple(recognition_keywords or RECOGNITION_KEYWORDS)

    name_lower = column_name.lower()
    if column_name in demographic_exact or any(
        keyword in name_lower for keyword in demographic_keywords
    ):
        return "demographics"
    if any(keyword in name_lower for keyword in enjoyment_keywords):
        return "enjoyment"
    if any(keyword in name_lower for keyword in familiarity_keywords):
        return "familiarity"
    if any(keyword in name_lower for keyword in recognition_keywords):
        return "recognition"
    return "other"


__all__ = [
    "assign_category",
    "DEMOGRAPHIC_EXACT",
    "DEMOGRAPHIC_KEYWORDS",
    "ENJOYMENT_KEYWORDS",
    "FAMILIARITY_KEYWORDS",
    "RECOGNITION_KEYWORDS",
]
