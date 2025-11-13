# Stage 2 Enjoyment Survey Schema Checklist

## Source Assets Reviewed
- Notebook: `analysis/assemble_uv.ipynb` — Stage 2 block loads Stage 1 demographics, melts survey matrices, and exports Stage 2 aggregates/open-ended tables.
- Stage 2 outputs: `results/uv_stage2.csv`, `results/uv_stage2_features.csv`, `results/uv_stage2_open_ended.csv`, `results/uv_stage2_issues.csv` (notes respondent `35` missing features).
- Metadata lookups: `analysis/support/survey_columns_by_group.csv`, `analysis/support/survey_columns_unique.csv`, `data/survey_column_rename.csv`, `data/stimulus_rename.csv`, `data/survey_questions.csv`.
- Stage 1 demographics + exposure map: `results/uv_stage1.csv`.
- Raw survey references: MERGED TSVs (`MERGED_SURVEY_RESPONSE_MATRIX-*.txt`) referenced in Stage 2 pipeline **not present** in repo; follow-up required before re-processing.

## Existing Helper Coverage
- `wbdlib.survey`: ingestion utilities (`load_survey_matrix`, `normalize_ids`, familiarity / recency parsing) leveraged in notebook Stage 2 block.
- `wbdlib.uv`: joining utilities to merge Stage 1 demographics and to standardize short/long titles.
- `wbdlib.constants`: normalization enums (e.g., yes/no values) used during melt/scoring.

## Proposed Long-Form Export Schema
Common keys and provenance:
1. `submitted_timestamp` — parsed from raw TSV submission columns (requires UTC normalization).
2. `respondent` — zero-padded string (Stage 1 key).
3. `group` — Stage 1 exposure group (A–F).
4. `stimulus_form` — `Short Form` / `Long Form` from Stage 1 lookup.
5. `stimulus_title` — harmonized title (e.g., `Mad Max`, `The Town`, `Abbot Elementary`).
6. `questionnaire` — Stage 2 instrument label (e.g., `MERGED_SURVEY_RESPONSE_MATRIX-A2`).
7. `question_code` — canonical code (`E1`, `F1`, `WBD1`, etc.).
8. `question_text` — friendly prompt text sourced via rename map / `survey_questions.csv`.
9. `question_type` — bucket (`likert`, `binary`, `open_ended`, `familiarity`).
10. `subscale` — Stage 2 composite grouping (`Enjoyment`, `Attention`, `Connection`, etc.).
11. `category` — high-level enjoyment vs familiarity classification (from `survey_columns_by_group.csv`).
12. `accuracy` — flag for directionality (where available in rename maps).
13. `response_raw` — unprocessed text/numeric response from raw TSV.
14. `response_clean` — trimmed/normalized string (title-case, whitespace cleaned).
15. `response_numeric` — float/int for likert/familiarity items (NaN for text).
16. `score_value` — populated from Stage 2 composite or derived metrics when applicable.
18. `score_method` — source label (`stage2_likert`, `stage2_composite` etc.).
19. `score_explanation` — short note describing how the score was assembled.
20. `source_path` — original MERGED TSV file name.

## Join & Enrichment Strategy
- Base long-form keyed on (`respondent`, `survey_file`, `question_code`).
- Attach Stage 1 demographics via `respondent`.
- Map metadata via `survey_columns_by_group.csv` (join on group + raw column) and `survey_column_rename.csv` for human-readable text.
- Append composite metrics by melting `results/uv_stage2_features.csv` (columns ending `_Count`, `_Sum`, `_Mean`, `_Normalized`, `_EnjoymentComposite_*`, familiarity composites, etc.) into tidy rows aligned with question codes.
- Merge open-ended text from `results/uv_stage2_open_ended.csv` on respondent & stimulus code, exposing them as `response_raw` entries for `E16` prompts.
- Carry issue flags from `results/uv_stage2_issues.csv` into a `data_quality_flag` column for affected respondents/questions.

## Data Gaps & Follow-Ups
- MERGED TSV survey sources missing from repo — request archived copies or confirm location before any re-extraction.
- Respondent `35` missing Stage 2 features—decide on exclusion note or locate raw submission.
- Legacy references to `uv_stage2_full_*` outputs deprecated; ensure downstream notebooks point to new long-form export name (proposed `results/stage2_enjoyment_responses_long.csv`).

## Readiness Notes
- Column naming conventions align with Stage 2 composites already consumed by downstream analysis notebooks.
- Scoring fields can reuse existing normalized values; no re-run of composite calculators required if we reshape `uv_stage2_features.csv`.
- Need to document timestamp dedupe policy (Stage 2 block uses submission timestamp to drop stale rows) when writing README.
