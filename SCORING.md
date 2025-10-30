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
- Map each cleaned F2 response to a 0–4 recency scale:
  - `I don't remember` / `More than 6 months ago` → 0
  - `More than 3 months ago` → 1
  - `Within the past 3 months` → 2
  - `Within the past month` → 3
  - `Within the past week` → 4
- Any response not in the mapping tables remains `NaN` to highlight unmapped text for future review.

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
