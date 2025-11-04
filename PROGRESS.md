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

### Stage 2: Exposure-Day Survey Metrics
- Reload the Stage 1 demographic baseline at the start of the stage so respondent metadata remains authoritative during survey merges.
- Normalize each `MERGED_SURVEY_RESPONSE_MATRIX-*.txt` surface (one per group) by trimming headers, coercing respondent identifiers to strings, and mapping raw question headers through `survey_column_rename_stage3.csv` into canonical targets.
- Build parsers for Likert scales, familiarity prompts (`F1`/`F3`), and recency checks (`F2`), including keyword backstops, polarity handling, and clipping to the 0–4 range.
- Deduplicate to one numeric survey record per respondent, split open-ended responses into `survey_open_ended`, and left-join the engineered metrics onto the Stage 1 baseline to produce `results/uv_stage2_full_uv.csv`, `results/uv_stage2_full_features.csv`, and `results/uv_stage2_full_open_ended.csv` accompanied by `results/uv_stage2_full_issues.csv` for audit.
- Integrate screening familiarity composites from `results/individual_composite_scores.csv`, canonicalizing title strings and inferring presentation form per respondent before emitting `{form}_{title}_Screening_Familiarity_{question_code}` columns.

### Sensor Feature Archive (Legacy Stage 2)
- Finalized helper stack: `read_imotions`, `prepare_stimulus_segment`, `compute_sensor_features`, and the orchestration wrapper `run_sensor_feature_pipeline`.
- The pipeline validates sensor coverage per respondent, auto-detects EEG alias columns, handles long-form key-moment windowing, and computes FAC/EEG/GSR/ET metrics with unified naming.
- Executed `run_sensor_feature_pipeline()` across all respondents (83 total); results archived at:
  - `results/uv_stage2_full_features.csv`
  - `results/uv_stage2_full_uv.csv`
  - `results/uv_stage2_full_issues.csv` (38 rows documenting missing sensors, unmapped stimuli, or empty windows).
- Uses timestamped fallback filenames and manual `gc.collect()` guards to keep batch processing stable; retained here for reference should sensor features be reintegrated later.

### Stage 3: Post Questionnaire Recognition
- Stage 3 now ingests the post-viewing questionnaire exports under `data/Post/`, collapsing duplicate headers and aligning responses to `post_survey_map.csv` via the shared `question_code` column.
- `uv_stage1.csv` is reloaded as the ground truth for respondent group assignment and Short/Long form exposure titles before any post data is parsed.
- Parsed records capture binary accuracy, confidence, and composite scores for each question, normalize respondent IDs, and attach the relative path of the originating CSV for traceability (`post_survey_source_path`).
- Category labels from the map are remapped (`key` ➜ `wb-key`, `seen` ➜ `wb-notKeySeen`, `unseen` ➜ `wb-notKeyUnseen`, `fake` ➜ `distractor`, `distractor` ➜ `comp-key`, `distractor2` ➜ `comp-notKeySeen`).
- For Post recognition composites, questions tagged `key`/`seen` are restricted to the respondent’s Stage 1 Long/Short titles so the aggregates emit as `{form}_{category}_Post_Recognition_{Statistic}`, while the remaining categories (`unseen`, `fake`, `distractor`, `distractor2`) collect across all appearances and emit as `{category}_Post_Recognition_{Statistic}`.
- Added a guard that only merges post-recognition responses when the Stage 1 group matches the group encoded in the source filename, skipping mismatched respondents (currently 6, 116, and 117) and logging the exclusion.
- The aggregated feature matrix is merged back onto the Stage 1 baseline and written to `results/uv_stage3.csv`, with companion issues captured in `results/uv_stage3_issues.csv` for diagnostics.
- Issues are surfaced whenever binary or confidence responses are missing, when forms must fall back to the group stimulus map, or when respondent groups are absent from both Stage 1 and the filename.

### Notebook Outputs
- `full_features` dataframe currently holds 1,076 Stage 2 feature columns aligned to 83 respondents.
- `full_issues` records outstanding data gaps per respondent/stimulus to triage before downstream modeling.
- `full_uv` merges Stage 1 demographics with Stage 2 features, providing the latest unified view snapshot.

### UV Merge Snapshot
- Combines the Stage 2 survey metrics and Stage 3 post-recognition composites back onto the Stage 1 demographic baseline.
- Highlights respondent-level discrepancies (duplicates, missing exposures, mismatched form assignments) in `results/merge_issues.csv` while emitting the consolidated UV at `results/uv_merged.csv`.
- Provides a quick audit path to ensure category-level recognition aggregates align with survey familiarity measures after the latest pipeline simplifications.

### Variables in Notebook Session
- `uv_stage1` and `uv` hold the demographic dataset; manual overrides are applied in place.
- `stimulus_summary` remains available for join operations if further timing diagnostics are needed.
- `full_features`, `full_uv`, and `full_issues` persist in memory for quick inspection during issue resolution.

## Next Steps
1. Review `results/uv_stage2_full_issues.csv` to reconcile missing sensor streams or unmapped stimuli (38 entries).
2. Confirm downstream consumers ingest the new `uv_stage2_full_uv.csv` and coordinate with analytics leads on required feature subsets.
3. Plan integration of survey/self-report datasets (e.g., `data/Export/.../Survey/`) alongside the Stage 2 metrics for the full UV.

---

## Pipeline Restructure (2025-11-03)
- Archived the legacy Stage 2 sensor feature pipeline in `analysis/assemble_uv.ipynb`. Stage numbering now aligns to data sources: Stage 1 (demographics), Stage 2 (exposure-day survey metrics), Stage 3 (post questionnaire recognition features).
- Stage 2 notebooks cells now reload `results/uv_stage1.csv` as the authoritative base before merging survey features and writing `uv_stage2.csv`, `uv_stage2_features.csv`, and `uv_stage2_issues.csv`.
- Stage 3 cells follow the same pattern, reloading Stage 1, engineering recognition metrics directly from the post questionnaire exports, and emitting `uv_stage3.csv` plus `uv_stage3_issues.csv`.
- Added a new "UV Merge" section that reads `uv_stage2.csv` and `uv_stage3.csv`, compares Stage 1 metadata for inconsistencies, and produces `uv_merged.csv` alongside `merge_issues.csv` to track duplicates, missing respondents, or baseline mismatches.

## Stage 1 Grid Enhancements (2025-11-03)
- Normalized the headers from `data/grid.csv`, added the respondent-level `Comments` field as `grid_comments`, and preserved it through the Stage 1 merge so contextual notes surface in `results/uv_stage1.csv`.
- Trimmed comment strings and ensured the new column is available to downstream stages for diagnostics and issue reconciliation.

---
Use this log to quickly re-establish context before continuing the analysis or before engaging with Copilot for future feature extraction tasks.