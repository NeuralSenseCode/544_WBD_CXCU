# Project Progress Log

- _Last updated: 2025-10-31_

This log captures the current state of analysis so future sessions can resume seamlessly. The immediate focus is reviewing full-cohort Stage 2 results and addressing the logged issues.

---

## Repository Setup
- Added `METHOD.md` documenting the unified view (UV) methodology, including naming conventions (`{form}_{title}_{sensor_type}_{metric}_{method}`), baseline respondent columns, and integration workflow guidance.
- Updated `.gitignore` so that only `data/Export/` is excluded while other files in `data/` remain trackable. This keeps raw sensor exports out of Git but allows reference tables (e.g., `stimulus_rename`, `key_moments`) to be versioned.
- Committed and pushed all current changes to `master` (commit `da6126e`).

## Data Assets Added
- `data/stimulus_rename.csv` contains group-specific stimulus names mapped to canonical titles and presentation forms (`Long` vs `Short`).
- `data/key_moments.csv` lists long-form stimuli with lead-up duration and key-moment duration to align short-form clips with the relevant segment of the long cut.

## Notebook: `analysis/assemble_uv.ipynb`
The notebook is organized into sections with the active work under **Feature Extraction**.

### Stimulus Duration Scan
- Located one sensor CSV per group (Groups A–F) via filesystem crawl.
- Used `read_imotions` to ingest each sample file.
- Calculated stimulus durations per file using the `Timestamp` column without cross-group aggregation.
- Produced `stimulus_summary` (36 rows) with columns:
  - `group`
  - `stimulus_name`
  - `duration_seconds`
  - `duration_minutes`
- Verified each group contains six unique stimuli and exported the table to `results/stimulus_summary.csv`.

### Annotation Context
- Documented how `stimulus_rename` and `key_moments` support mapping raw stimuli to titles/forms and identifying key-moment windows for long-form content.

-### Stage 1: Demographics
- Scanned **every** sensor export under `data/Export/Group */Analyses/*/Sensor Data/`.
- Introduced the lightweight `read_imotions_metadata` helper so the demographic pass only parses the header rows (no full CSV load) while still extracting:
  - `Study name`
  - `Respondent Name`
  - `Respondent Group`
  - `Recording time`
- Implemented robust parsing to clean metadata quirks:
  - Removed trailing comma padding.
  - Derived `group` from study name (final letter) or fallback path.
  - Captured numeric respondent IDs (handles up to 3 digits).
  - Split recording timestamp into `date_study` and `time_study`, converting to America/Chicago timezone.
- Treated `data/grid.csv` as the system of record for demographics: renamed `QB2. Age` ➜ `age`, `QB2. Age.1` ➜ `age_group`, `QA2. Gender` ➜ `gender`, and trimmed all string responses before coercing numeric fields.
- Joined the renamed grid slice onto `uv_stage1`, filling `age`, `gender`, `age_group`, `ethnicity`, `income_group`, `content_consumption`, and the `%` split columns while warning when any expected grid columns are missing.
- Applied manual gender overrides for respondents `8`, `56`, `16`, `6`, `46`, `69`, `44`, and `50` per client guidance so downstream reporting matches prior deliverables.
- Dropped duplicate grid respondents after coercing the identifier to string and exported the refreshed demographic UV snapshot to `results/uv_stage1_demographics.csv`.
- Verified there are no duplicate respondents.

### Stage 2: Sensor Data (Full Sample)
- Finalized helper stack: `read_imotions`, `prepare_stimulus_segment`, `compute_sensor_features`, and the new orchestration wrapper `run_sensor_feature_pipeline`.
- The pipeline now validates sensor coverage per respondent, auto-detects EEG alias columns, handles long-form key-moment windowing, and computes FAC/EEG/GSR/ET metrics with unified naming.
- Executed `run_sensor_feature_pipeline()` across all respondents (83 total); results exported to:
  - `results/uv_stage2_full_features.csv`
  - `results/uv_stage2_full_uv.csv`
  - `results/uv_stage2_full_issues.csv` (38 rows documenting missing sensors, unmapped stimuli, or empty windows).
- Implemented safe CSV writing with timestamped fallbacks to avoid permission clashes and added `gc.collect()` guards to keep memory pressure manageable during batch processing.

### Stage 3
- Loaded the Stage 3 rename map (`data/survey_column_rename_stage3.csv`) and question catalog (`data/survey_questions.csv`) to construct a metadata lookup covering target columns, question types, polarity flags, and enjoyment subscales.
- Processed every `MERGED_SURVEY_RESPONSE_MATRIX-*.txt` file under `data/Export/Group */Analyses/*/Survey/`, normalizing respondent IDs, harmonizing group/study/gender fields, and applying group-specific column renaming.
- Built parsers for Likert-style responses, including keyword fallback scoring, reverse-coding for negatively keyed items, and specialized scorers for familiarity (`F1`/`F3`) and recency (`F2`).
- Computed enjoyment subscale aggregates and standardized familiarity composites (sum/count/mean/normalized) for each stimulus prefix while preserving raw open-ended responses in a separate frame.
- Deduplicated to a single numeric survey record per respondent, split open-ended text columns into `survey_open_ended`, and merged the numeric features with the existing unified view (`full_uv` when available, otherwise Stage 1 demographics).
- Hardened the F1/F2 familiarity remapping to enforce the 0–4 scale for both prompts, including raw numeric prefixes (for example "5.0"), and added defensive clipping to prevent scale drift in future reruns.
- Recomputed enjoyment composites so `_Sum` reflects the raw (pre-polarity) totals, `_Corrected` and `_Mean` use polarity-adjusted scores, `_Normalized` scales the raw totals, and the new `_NormalizedCorrected` column scales the corrected totals.
- Integrated screening familiarity composites from `results/individual_composite_scores.csv`, canonicalizing title strings (collapsing `Abbot`/`Abbott`) and inferring `Long`/`Short` forms per respondent group before emitting `{form}_{title}_Screening_Familiarity_{question_code}` columns.
- Exported Stage 3 deliverables to `results/uv_stage3_full_features.csv`, `results/uv_stage3_full_open_ended.csv`, and `results/uv_stage3_full_uv.csv`; merge warnings surface any duplicate respondent entries for follow-up. The latest run saved `results/uv_stage3_full_features_20251030155141.csv` after a permission fallback and now reports 356 engineered survey columns.
- Latest export run saved the feature matrix as `results/uv_stage3_full_features_20251030152658.csv` because the base filename was in use; contents mirror the corrected schema described above.

### Notebook Outputs
- `full_features` dataframe currently holds 1,076 Stage 2 feature columns aligned to 83 respondents.
- `full_issues` records outstanding data gaps per respondent/stimulus to triage before downstream modeling.
- `full_uv` merges Stage 1 demographics with Stage 2 features, providing the latest unified view snapshot.

### Stage 4: Post Questionnaire (Planned)
- Goal is to ingest the seven-day Post questionnaire exports located under `data/Recall/` for Groups A–F.
- The canonical item map now lives at `data/post_survey_map.csv`; we rely on its `question_code`-ready numbering to align variant wordings across groups before feature extraction.
- Plan to coerce respondent identifiers as strings before joins to avoid dropping participants with padded IDs; merge on (`respondent`, `group`).
- Will generate Post-specific feature and issues outputs (`results/uv_stage4_post_features.csv`, `results/uv_stage4_post_issues.csv`) and append the enriched UV snapshot to `results/uv_stage4_full_uv.csv` once validated.
- Pending validation steps include confirming questionnaire completeness per group and drafting helper functions for accuracy and confidence scoring keyed off `question_code`.
- Verification scripts now read the canonical map directly, collapsing duplicate headers in the raw exports, confirming inferred response types against the map for audit purposes, and emitting an audited copy to `results/post_question_map.csv` when rerun.

### Variables in Notebook Session
- `uv_stage1` and `uv` hold the demographic dataset; manual overrides are applied in place.
- `stimulus_summary` remains available for join operations if further timing diagnostics are needed.
- `full_features`, `full_uv`, and `full_issues` persist in memory for quick inspection during issue resolution.

## Next Steps
1. Review `results/uv_stage2_full_issues.csv` to reconcile missing sensor streams or unmapped stimuli (38 entries).
2. Confirm downstream consumers ingest the new `uv_stage2_full_uv.csv` and coordinate with analytics leads on required feature subsets.
3. Plan integration of survey/self-report datasets (e.g., `data/Export/.../Survey/`) alongside the Stage 2 metrics for the full UV.

---
Use this log to quickly re-establish context before continuing the analysis or before engaging with Copilot for future feature extraction tasks.