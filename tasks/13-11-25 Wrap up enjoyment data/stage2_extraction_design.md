# Stage 2 Enjoyment Survey Extraction Design

## Objectives
- Produce a deterministic Stage 2 long-form export without re-running scorers unless new raw submissions arrive.
- Reuse existing Stage 2 outputs (`uv_stage2.csv`, `uv_stage2_features.csv`, `uv_stage2_open_ended.csv`, `uv_stage2_issues.csv`) and Stage 1 demographics (`uv_stage1.csv`).
- Keep all logic in `analysis/assemble_uv.ipynb` under the Stage 2 section, delegating reusable routines to `wbdlib` where needed.

## Pipeline Overview (Notebook Cells)
1. **Load prerequisites**
   - Reuse Stage 2 dataframes produced earlier in the notebook (`uv_stage2_df`, `uv_stage2_features_df`, `uv_stage2_open_ended_df`, `uv_stage2_issues_df`).
   - Load Stage 1 demographic table (`uv_stage1_df`) if not already cached.
   - Load rename/lookups: `survey_columns_by_group.csv`, `survey_column_rename.csv`, `survey_questions.csv`, `stimulus_rename.csv`.
2. **Build response long-form frame**
   - Read raw Stage 2 response matrix output (if accessible) via `wbdlib.survey.load_survey_matrix`; otherwise reshape the tidy respondent-level frame from `uv_stage2_df`.
   - Melt responses to (`respondent`, `group`, `survey_file`, `raw_column`, `response_raw`).
   - Normalize identifiers and attach metadata (question codes, friendly text, stimulus titles).
3. **Attach scoring metadata**
   - Melt `uv_stage2_features_df` to long form for numeric metrics (composites, counts, sums) tagging `score_method`.
   - Merge per-question derived values (`score_value`, `score_confidence`, `score_explanation`).
   - Append open-ended text responses from `uv_stage2_open_ended_df` for `E16` items, marking `question_type="open_ended"` and populating `response_raw` and `response_clean`.
4. **Enrich with Stage 1 context**
   - Join Stage 1 demographics/form assignments via `respondent` to populate group, form, and harmonized title columns.
   - Apply `stimulus_rename.csv` mapping to ensure long/short titles align with Stage 2 composites.
5. **Quality tagging**
   - Left join `uv_stage2_issues_df` to surface `data_quality_flag`, `issue_code`, `issue_note`.
   - Add coverage diagnostics (missing scores, missing raw response) for validation step.
6. **Finalize export**
   - Order columns according to schema checklist.
   - Write CSV to `results/enjoyment_responses_long.csv` (temporary location) and copy to task folder for review.
   - Persist ancillary diagnostics (duplicates, missing metadata) as separate CSVs if non-empty.

## Proposed Helper Functions
Implement in `analysis/assemble_uv.ipynb` unless refactoring to `wbdlib` becomes necessary.

- `load_stage2_long_source()`
  - Inputs: optional path overrides for Stage 2 output CSVs.
  - Behavior: returns dictionary of dataframes (`stage2_features`, `stage2_open_ended`, `stage2_issues`, `stage1_demographics`).

- `reshape_stage2_responses_long(stage2_df, metadata_df)`
  - Uses `pd.melt` on respondent-level responses, normalizes column names, attaches question metadata.
  - Handles missing raw matrix by deriving from `stage2_df` columns with prefix `survey__` (confirm actual naming before coding).

- `attach_stage2_scores(long_df, features_long_df)`
  - Merges per-question scores, including composite tags and `score_method` mapping.

- `append_open_ended(long_df, open_text_df)`
  - Appends rows for open-ended questions, ensuring consistent schema.

- `apply_stage1_enrichment(long_df, stage1_df, stimulus_map_df)`
  - Adds group, stimulus form, titles, harmonized naming.

Each helper should live in the notebook initially; if reused elsewhere, promote to `wbdlib/uv.py` with docstrings.

## Normalization Rules
- Respondent IDs: cast to string, left-pad to 3 digits (`zfill(3)`), strip whitespace.
- Group labels: uppercase single letter; derive from Stage 1 lookup rather than trusting Stage 2 columns.
- Timestamps: convert to timezone-aware UTC using `pd.to_datetime(..., utc=True)` when raw submission timestamp exists.
- Stimulus titles: map via `stimulus_rename.csv` and Stage 1 exposures; maintain both `stimulus_title` and `stimulus_form`.
- Question codes: rely on `survey_column_rename.csv` canonical code; ensure duplicates resolved by prefer latest rename entry.
- Response normalization: trim whitespace, consolidate multi-select separators to semicolon-space, preserve original raw field separately.
- Score values: ensure numeric columns cast to `float`; leave `NaN` for non-numeric responses.
- Boolean flags: represent with lowercase `true`/`false` strings for readability in client CSV.

## Join Strategy
- Primary key: (`respondent`, `question_code`, `stimulus_title`, `survey_file`).
- Metadata join: `raw_column` + `group` -> `survey_columns_by_group.csv` to fetch code/category/subscale.
- Stage 1 join: `respondent` -> `uv_stage1.csv` to acquire group, exposure titles, form.
- Features join: melt `uv_stage2_features.csv` to (`respondent`, `feature_name`, `value`) and map `feature_name` to question codes via lookup table defined inline.
- Open-ended join: `respondent`, `stimulus_id` -> open text table.
- Issues join: `respondent` -> Stage 2 issues table.

## Validation Targets
- Row count >= (number of respondents * number of Stage 2 questions) minus known gaps noted in issues file.
- Unique key check on (`respondent`, `question_code`, `stimulus_title`, `survey_file`).
- Confirm all question codes present in metadata file; flag any orphaned columns.
- Compare aggregated means/medians against `uv_stage2_features.csv` to ensure alignment.

## Risks & Mitigations
- **Missing raw MERGED matrices**: fallback path uses `uv_stage2_df`; document that raw re-extraction is blocked pending archive retrieval.
- **Respondent 35**: propagate issue flag and exclude from scoring calculations if data absent; note in final README.
- **Metadata drift**: add assertion to ensure `survey_column_rename.csv` covers every melted column.

## Deliverables from Step 2
- Updated notebook cells (planning comments outlining helper usage).
- This design document reviewed with stakeholders.
- Task plan milestone satisfied; ready to build implementation in Step 3.
