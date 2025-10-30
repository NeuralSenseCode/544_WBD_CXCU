# Scoring Reference

## Familiarity (F1, F2, C1)

### Source Items
- **F1 (Familiarity prompt):** Survey columns ending with `_Familiarity` (e.g., `Q3_1_1_The Dark Knight_Familiarity`).
- **F2 (Last Watched prompt):** Survey columns ending with `_Lastwatched` (e.g., `Q3_1_2_The Dark Knight_Lastwatched`).
- **Respondent identifier:** Original survey column `No.` is preserved as `respondent` in exported tables.

### Text Normalization
- Normalize Unicode punctuation (curly quotes, smart apostrophes) to ASCII equivalents.
- Collapse internal whitespace and trim leading/trailing spaces.
- Apply targeted title corrections to ensure canonical forms (e.g., all "Dark Knight" variants become `The Dark Knight`).

### Likert Remapping to Numeric
- Map each cleaned F1 response to a 0–4 familiarity scale:
  - `Never heard of it (not familiar)` → 0
  - `Heard of it, but never watched it` / `Heard of it only` → 1
  - `Seen a clip or part of it` variants → 2
  - `Watched it in full (just once)` / single-episode responses → 3
  - `Watched multiple episodes` / "Very familiar" variants → 4
  - If a response begins with a numeric token (for example `"5"`, `"5.0"`), subtract 1 and clip to `[0, 4]` to collapse the raw 1–5 scale onto 0–4.
- Map each cleaned F2 response to a 0–4 recency scale:
  - `I don't remember` / `More than 6 months ago` → 0
  - `More than 3 months ago` → 1
  - `Within the past 3 months` → 2
  - `Within the past month` → 3
  - `Within the past week` → 4
  - Numeric-prefixed answers (including variants like `"4 = Past month"`) also subtract 1 and are clipped to `[0, 4]`.
- Any response not in the mapping tables (or convertible to a leading numeric value) remains `NaN` to highlight unmapped text for future review.

### Numeric Data Sets
- `df_scores`: Numeric version of the survey with passthrough columns (`Name`, `respondent`) followed by standardized `Q*_Familiarity` and `Q*_Lastwatched` columns.
- `df_analysis`: Group-labelled columns for reporting, renamed to `{Group}_{Title}_{Metric}` (for example, `A_Mad Max Fury Road_Familiarity`).

### Composite Construction (C1)
- For every title with F1 and/or F2 data, compute `C1` as:

  ```text
  C1 = coalesce(F1, 0) + coalesce(F2, 0)
  ```

  where missing familiarity or last-watched values are treated as 0 during the sum.
- Composite columns are named `{Title}_composite` inside `df_analysis` and exported as `{Title}_Survey_Familiarity_C1`.

### Export Schema
- Output file: `results/individual_composite_scores.csv`.
- Columns: `Name`, `respondent`, and for each tracked title (e.g., Mad Max Fury Road, The Town, Abbot Elementary) the trio:
  - `{Title}_Survey_Familiarity_F1`
  - `{Title}_Survey_Familiarity_F2`
  - `{Title}_Survey_Familiarity_C1`
- Column order is fixed to maintain repeatable downstream merges.

### Maintenance Notes
- Extend familiarity or last-watched mappings by appending entries to the explicit dictionaries in the notebook (`familiarity_explicit`, `lastwatched_explicit`).
- When adding titles, ensure the metadata file `data/movies_series_list.csv` carries the canonical title and group so the renaming and grouping logic remain consistent.
- Re-run the notebook end-to-end before distributing updated exports to guarantee mapping statistics and composite calculations reflect the new definitions.

# Stage 3
- The Stage 3 export now includes the companion columns `{Title}_Survey_Familiarity_C1_Count` (number of non-null familiarity/recency answers contributing to the composite) and `{Title}_Survey_Familiarity_C1_Normalized`, where the normalized score is computed as `clip(C1 / (4 * Count), 0, 1)`.

## Enjoyment Likert Remapping
- Stage 3 processing converts every survey column tagged as a Likert item to numeric form before aggregation. During this pass the table retains the original text values separately so polarity corrections can always reference the raw response wording.
- Primary parsing rule: extract the leading integer token (for example `"5 = Strongly Agree" → 5`). Decimal prefixes are supported (for example `"4.0"`).
- Fallback keyword mapping supports free-text variants (case-insensitive):
  - `"strongly disagree" → 1`
  - `"disagree" → 2`
  - `"neither agree nor disagree" → 3`
  - `"agree" → 4`
  - `"strongly agree" → 5`
- Items flagged as negatively worded in `data/survey_questions.csv` are reverse-scored using `6 - value` after the initial numeric conversion. Composite metrics (`..._Survey_EnjoymentComposite_*`) retain the raw sum (`_Sum`) on the original response scale, expose a `_Corrected` sum after polarity adjustment, and deliver two normalizations:
  - `_Normalized` rescales the raw sum (pre-polarity) back onto `[0, 1]`.
  - `_NormalizedCorrected` rescales the polarity-adjusted `_Corrected` sum onto `[0, 1]`.
  The composite mean (`_Mean`) is computed from the corrected values.
- Familiarity prompts (`F1`, `F3`) and recency prompts (`F2`) reuse the explicit 0–4 mappings described earlier; any residual numeric prefix is honored when no keyword match exists.

## Subscale and Composite Features
- For each stimulus prefix (for example `Long_The Town` or `Short_Mad Max`), all Likert enjoyment items are grouped by their subscale label from `survey_questions.csv`.
- Let `S` denote the set of columns in a given subscale. Stage 3 derives:
  - `Sum = Σ value_i` treating missing answers as excluded.
  - `Count = |{ value_i ∈ S : value_i is not NaN }|`.
  - `Mean = Sum / Count` when `Count > 0`, else `NaN`.
  - `Normalized = clip((Sum - Count) / (4 * Count), 0, 1)` with clipping applied only when `Count > 0`. This rescales the 1–5 Likert range to 0–1 by subtracting the minimum possible total (`Count`) and dividing by the span (`4 * Count`).
- Column naming follows `{Prefix}_Survey_{Subscale}_{Metric}` where `{Metric}` ∈ {`Sum`, `Count`, `Mean`, `Normalized`}.
- A parallel set of metrics aggregates **all** enjoyment Likert items per prefix (irrespective of subscale) using the label `EnjoymentComposite` to provide an overall enjoyment score.

## Open-Ended Responses
- Survey questions labeled as `open ended` are preserved verbatim and exported to `results/uv_stage3_full_open_ended.csv` alongside respondent metadata.
- The numeric feature matrix (`results/uv_stage3_full_features.csv`) excludes these free-text columns but retains the engineered metrics described above.

## Screening Familiarity Integration
- The screening composites in `results/individual_composite_scores.csv` are merged into the Stage 3 feature matrix after canonicalizing title strings (collapsing spelling variants such as `Abbot` and `Abbott`).
- For each respondent, the Stage 1 demographic table supplies the group letter that, combined with `data/stimulus_rename.csv`, determines whether the screening response should be tagged as `Long` or `Short` form.
- Output column naming follows `{form}_{title}_Screening_Familiarity_{question_code}`, where `{question_code}` is the source suffix (`F1`, `F2`, or `C1`).
- Numeric values remain on the 0–4 familiarity scale. When both `F1` and `F2` are present the downstream Stage 3 pipeline also produces the additive composite `C1` for consistency with the in-session survey metrics.
