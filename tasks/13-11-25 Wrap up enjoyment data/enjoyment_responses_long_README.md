# Stage 2 Enjoyment Responses (Client Deliverable)

This document describes the structure, provenance, and validation notes for the Stage 2 enjoyment survey long-form export. The deliverable contains every enjoyment survey response (raw and derived) together with scoring context and stimulus metadata for Groups A–F.

## File summary

- **Primary file:** `results/stage2_enjoyment_responses_long.csv`
- **Preview copy:** `tasks/13-11-25 Wrap up enjoyment data/stage2_enjoyment_responses_long.csv`
- **Row count:** 18,367 (7,553 raw responses + 10,814 derived score rows)
- **Unique respondents:** 83
- **Source notebook:** `analysis/assemble_uv.ipynb` (Stage 2 Long-Form Export section)

## Column definitions

| Column | Description | Type / Values | Notes |
| --- | --- | --- | --- |
| `submitted_timestamp` | Submission timestamp for the source survey row | datetime (UTC-naïve) | Placeholder `NaT`; raw exports did not include timestamps |
| `respondent` | Participant identifier | string | Zero-padded (e.g., `001`); harmonised across stages |
| `group` | Study group | string | Uppercase letter `A`–`F` pulled from Stage 2 or Stage 1 lookup |
| `survey_group` | Original survey grouping label | string | Present when the wide export exposed the column |
| `survey_study` | Source study descriptor | string | Carries over from wide Stage 2 export |
| `survey_gender` | Stated gender | string | Optional column from Stage 2 survey |
| `survey_age` | Age entry | string | Optional column from Stage 2 survey |
| `stimulus_form` | Short vs. long cut | string | `Short Form`, `Long Form`; inferred from column name when metadata missing |
| `stimulus_title` | Canonical stimulus title | string | Normalised via helper mapping (e.g., `Mad Max`, `Abbot Elementary`) |
| `Short Form` | Short-form title assigned in Stage 1 | string | Retained for cross-stage joins |
| `Long Form` | Long-form title assigned in Stage 1 | string | Retained for cross-stage joins |
| `questionnaire` | Questionnaire label | string | Defaults to `Stage 2 Survey` |
| `source_path` | Relative path to originating survey file | string | Blank when wide export already aggregated responses |
| `question_code` | Canonical question identifier | string | Derived from rename map; fallback `UNKNOWN_<target_column>` if unmapped |
| `target_column` | Original wide-format column name | string | Matches header in `uv_stage2.csv` |
| `question_text` | Cleaned survey prompt | string | Pulled from `survey_questions.csv` when available |
| `question_type` | Survey question type | string | Values such as `likert`, `familiarity`, `open ended`, `binary`, `unknown` |
| `subscale` | Measurement subscale | string | From rename map (e.g., `overall enjoyment`, `narrative`) |
| `category` | Human-readable category | string | Underscores replaced with spaces |
| `accuracy` | Expected answer orientation | string | Populated when Stage 2 issues required a flag; otherwise blank |
| `response_raw` | Raw survey value | string | Direct string from wide export |
| `response_clean` | Normalised response | string | Trimmed string or `NaN` when blank |
| `response_numeric` | Numeric interpretation | float | Likert and familiarity values brought across from features export |
| `score_value` | Scoring metric | float | Mirrors `response_numeric` for responses, or feature score for derived rows |
| `score_method` | Provenance of `score_value` | string | `stage2_likert`, `stage2_familiarity`, `stage2_open_ended`, `stage2_response`, or feature-specific names |
| `score_stat` | Statistic descriptor | string | Populated for derived metrics (e.g., `zscore`, `mean`) |
| `score_explanation` | Human-readable scoring note | string | Short description of the scoring method |
| `value_kind` | Record type flag | string | `response` or `score` |
| `data_quality_flag` | Data quality indicator | string | `true` when respondent present in Stage 2 issue log; otherwise `false` |
| `issue_code` | Concatenated issue notes | string | Semi-colon list sourced from `uv_stage2_issues.csv` |

### Category mapping

- `Short Form` / `Long Form` columns replicate Stage 1 canonical naming to support cross-stage comparisons.
- `stimulus_form` is inferred from metadata or the `target_column` prefix (`Short_` / `Long_`).
- `question_code` falls back to `UNKNOWN_<column>` when metadata is absent; addressable by enriching `survey_column_rename.csv`.

## Supporting assets

- `results/uv_stage2.csv` — wide-format Stage 2 survey responses.
- `results/uv_stage2_features.csv` — derived metrics and numeric mappings.
- `results/uv_stage2_open_ended.csv` — Stage 2 open-ended responses.
- `results/uv_stage2_issues.csv` — respondent-level data quality notes.
- `results/uv_stage1.csv` — Stage 1 demographic roster used for joins.
- `data/survey_column_rename.csv`, `data/survey_questions.csv` — metadata lookups.

## Scoring

### Likert and familiarity items
- Likert items carry `score_method = stage2_likert`; values range 1–5 with polarity handled upstream in features export.
- Familiarity items use `score_method = stage2_familiarity`; values reflect normalised familiarity scores.

### Open-ended responses
- Text responses keep `value_kind = response` with `score_method = stage2_open_ended` and empty `score_value`.

### Derived metrics
- Melted from `uv_stage2_features.csv` when helper parsing resolves metric metadata (instrument, statistic).
- Eight feature columns lacked parseable names during export and were skipped (see notebook log for exact headers).

## Validation

- Notebook Cell 38 (execution count 48) summarises QA checks and writes `tasks/13-11-25 Wrap up enjoyment data/stage2_validation_summary.json`.
- Respondent sets between wide and long exports match exactly (83 IDs).
- Expected response slots (wide rows × response columns) equal observed response rows (7,553); no duplicate respondent/target pairs remain.
- Derived score rows total 10,814 after filtering unparseable metrics.

## Known caveats

1. Twenty-three Stage 2 columns still lack metadata coverage in `survey_column_rename.csv`; resulting rows use fallback `question_code` values.
2. `uv_stage2_issues.csv` flags one respondent with outstanding issues (`data_quality_flag = true`).
3. Raw MERGED Google Form TSV exports were not available in the repository, preventing timestamp backfill and independent repro of the wide export.
4. Empty `source_path` values indicate responses originated from the aggregated `uv_stage2.csv` rather than individual survey files.

## Recommended follow-ups

1. Extend the rename map and question catalog for the 23 unmapped columns, then rerun the Stage 2 export to eliminate `UNKNOWN_*` codes.
2. Investigate and document the respondent flagged in Stage 2 issues before client delivery.
3. Decide whether MERGED surveys need to be restored for archival reproducibility and timestamp enrichment.
