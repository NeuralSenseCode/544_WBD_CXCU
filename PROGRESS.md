# Project Progress Log

_Last updated: 2025-10-27_

This log captures the current state of analysis so future sessions can resume seamlessly. The goal is to continue Feature Extraction Stage 2 next.

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

### Stage 1: Demographics
- Scanned **every** sensor export under `data/Export/Group */Analyses/*/Sensor Data/`.
- Extracted metadata via `read_imotions` using keys:
  - `Study name`
  - `Respondent Name`
  - `Respondent Age`
  - `Respondent Gender`
  - `Respondent Group`
  - `Recording time`
- Implemented robust parsing to clean metadata quirks:
  - Removed trailing comma padding.
  - Derived `group` from study name (final letter) or fallback path.
  - Captured numeric respondent IDs (handles up to 3 digits).
  - Converted age to integer, gender to title-case categories (`Male`, `Female`, `Other`).
  - Split recording timestamp into `date_study` and `time_study`, converting to America/Chicago timezone.
- Constructed `uv_stage1` (and mirrored `uv`) with columns:
  - `source_file`
  - `group`
  - `respondent`
  - `age`
  - `gender`
  - `date_study`
  - `time_study`
- Verified there are no duplicate respondents.
- Applied manual gender overrides for respondents `8`, `56`, `16`, `6`, `46`, `69`, `44`, and `50` per client guidance.
- Enriched `uv_stage1` by joining the refreshed `data/grid.csv`, mapping the survey fields into `age_group`, `ethnicity`, `income_group`, `content_consumption`, and the `%` split columns (`content_consumption_movies`, `content_consumption_series`, `content_consumption_short`) with careful ID coercion and whitespace cleanup to prevent nulls.
- Exported the demographic UV snapshot to `results/uv_stage1_demographics.csv` (now including the supplemental survey fields).

### Variables in Notebook Session
- `uv_stage1` and `uv` currently hold the demographic dataset; manual overrides are applied in place.
- `stimulus_summary` is available for joining with external mappings in later steps.

## Next Steps (Stage 2 Preview)
1. Join `stimulus_summary` with `stimulus_rename` to attach canonical titles and forms.
2. Incorporate `key_moments` to align long-form stimuli with short-form segments.
3. Begin extracting sensor-based features per `{form}_{title}` using the naming convention, populating additional columns in `uv`.
4. Integrate survey/self-report datasets (e.g., `data/Export/.../Survey/`) and demographic tables (`results/uv_stage1_demographics.csv`).

---
Use this log to quickly re-establish context before continuing the analysis or before engaging with Copilot for future feature extraction tasks.