# Unified View (UV) Methodology

This document describes the standard approach for building a Unified View (UV) of mixed neurophysiological and survey data at the respondent level. The goal is to create a reusable template that can be applied across projects, ensuring that every data point linked to an individual is available in a single, analysis-ready table.

## Guiding Principles
- **Single source of truth**: Maintain one DataFrame named `uv` that represents the canonical dataset for downstream analysis.
- **Row-per-respondent schema**: Each row corresponds to exactly one respondent across all data modalities.
- **Column-level traceability**: Column names encode both provenance and measurement type, enabling quick identification of data origins and metric definitions.
- **Incremental assembly**: Build the UV iteratively, appending validated features from sensor streams, self-report instruments, and demographic records.

## Baseline Columns
Every project should populate the following respondent-level descriptors as early as possible. These fields establish consistent join keys and temporal context:
- `respondent`: Unique identifier for the participant.
- `age`: Respondent age at the time of data collection.
- `gender`: Self-reported or recorded gender descriptor.
- `group`: Experimental or stimulus group designation (single character recommended for compactness).
- `date_study`: Study completion date in ISO format (YYYY-MM-DD).
- `time_study`: Study completion time in HH:MM format (24-hour clock encouraged).

## Column Naming Convention
To support automated parsing the UV uses the following pattern for all derived measures:

```
{form}_{title}_{sensor}_{metric}_{method}
```

Where:
- `form` describes the presentation format (for example `Long`, `Short`, `Baseline`).
- `title` identifies the stimulus, survey construct, or demographic attribute. Use lowercase and separate words with spaces, camelCase, or hyphens rather than underscores (e.g., `mad max fury road`).
- `sensor` captures the modality or source stream. For Stage 2 sensor features this can be `EEG`, `GSR`, `ET`, or `FAC`; for other modalities retain existing labels such as `Survey` or `Demo`.
- `metric` captures the core signal dimension (e.g., `Engagement`, `PeakCount`, `BlinkCount`).
- `method` records the statistical operation applied (e.g., `Mean`, `Max`, `AUC`).

Use underscores *only* to separate the major segments shown above (`form_title_sensor_type_metric_method`). Within any single segment employ spaces, camelCase, or hyphens to maintain readability (for example `long_mad max fury road_EEG_Engagement_Mean`).

## Data Preparation Workflow
1. **Map raw stimuli**: Use `data/stimulus_rename.csv` to translate group-specific `SourceStimuliName` values into canonical titles and presentation forms (`Long`/`Short`).
2. **Align key moments**: Load `data/key_moments.csv` to capture long-form lead-up and key-moment durations so the short-form clip aligns with the correct long-form segment.
3. **Ingest iMotions exports**: Read sensor CSVs with `read_imotions`, which strips metadata headers and returns a clean DataFrame plus requested metadata. Treat `Timestamp` as milliseconds.
4. **Normalize metadata**: Standardize respondent IDs, group letters, demographic overrides, and timezone-aware study timestamps before merging any sensor features.



## Data Integration Workflow
1. **Initialize UV**: Create an empty DataFrame with the baseline columns. Populate respondent metadata from roster files or enrollment logs.
2. **Sensor ingestion**: Read raw exports using standardized readers (for example, `read_imotions`). Extract per-respondent, per-stimulus summaries and append as new columns following the naming convention.
3. **Survey merge**: Process self-report instruments, ensuring respondent identifiers align with the UV. Add each metric as a new column with `sensor_type` set to `Survey` or another appropriate label.
4. **Demographics and external data**: Join any additional contextual features (e.g., media familiarity scores, psychometrics). Prefix columns with `demo_` or another agreed tag for clarity.
5. **Validation**: After each integration step, confirm row counts, respondent coverage, and absence of duplicated identifiers. Document any exclusion criteria or imputations.
6. **Versioning**: Save periodic snapshots (CSV or Parquet) to the `results/` directory with timestamped filenames to preserve provenance while iterating.

### Stage 1 Demographics
- Use sensor metadata as the backbone for respondent IDs, group assignments, and study timestamps, relying on `read_imotions` to extract `Study name`, `Respondent Name`, `Respondent Group`, and `Recording time` while ignoring `Respondent Age` and `Respondent Gender` fields that frequently drift from grid answers.
- Treat `data/grid.csv` as the authoritative source for demographic attributes. Trim header whitespace, rename `QB2. Age` to `age`, `QB2. Age.1` to `age_group`, `QA2. Gender` to `gender`, and preserve the `Comments` field as `grid_comments` for qualitative context.
- Drop duplicate grid respondents after coercing the identifier to string, then left-join the cleaned grid slice onto `uv_stage1` so the demographic baseline fills `age`, `gender`, `age_group`, `ethnicity`, `income_group`, content-consumption measures, and the new `grid_comments` column without introducing parallel age fields.
- Apply manual overrides as needed to honour client-approved corrections, and persist the Stage 1 snapshot to `results/uv_stage1.csv` before downstream merges.

### Stage 2 Survey Feature Pipeline
- Reload `results/uv_stage1.csv` at the top of the stage to ensure a consistent respondent baseline before ingesting exposure-day survey exports.
- Normalise each TSV by trimming column names, coercing respondent identifiers to strings, and mapping raw question headers to canonical targets through `survey_metadata`.
- Split the cleansed survey frame into numeric features, composite scales, and open-ended responses; compute derived scores (Likert parsing, familiarity, recency, etc.) while logging any unmapped or duplicate respondents to `results/uv_stage2_issues.csv`.
- Write the consolidated Stage 2 products—`uv_stage2.csv`, `uv_stage2_features.csv`, and `uv_stage2_open_ended.csv`—so subsequent notebooks can join them without re-running the survey ETL.

### Stage 3 Post Questionnaire Integration
- **Objective**: Merge recognition metrics captured in the post-viewing questionnaire directly onto the Stage 1 baseline while keeping survey and demographic features intact.
- **Source files**: Use the `data/Post/Group *_ Post Viewing Questionnaire Part Two*.csv` exports, coercing respondent identifiers to strings and reloading `uv_stage1_demographics.csv` as the single source of truth for respondent group and Short/Long exposure titles before parsing.
- **Reference map**: Rely on `data/post_survey_map.csv` (supplemented by `results/post_question_map.csv`) keyed on `question_code` so variant wordings across groups continue to align.
- **Feature engineering**: Collapse duplicate headers, parse binary accuracy, confidence, and composite scores per respondent, and remap category labels with the agreed vocabulary (`key` ➜ `wb-key`, `seen` ➜ `wb-notKeySeen`, `unseen` ➜ `wb-notKeyUnseen`, `fake` ➜ `distractor`, `distractor` ➜ `comp-key`, `distractor2` ➜ `comp-notKeySeen`). Aggregate recognition composites with two paths: for `key`/`seen`, restrict to the respondent’s Stage 1 Long/Short titles so outputs follow `{form}_{category}_Post_Recognition_{Statistic}`; for `unseen`, `fake`, `distractor`, and `distractor2`, collect across all appearances and emit `{category}_Post_Recognition_{Statistic}` columns.
- **Alignment check**: Only accept recognition responses when the Stage 1 group matches the group parsed from the post questionnaire filename; mismatches are logged and the respondent is skipped to keep UV groups consistent.
- **Traceability**: Persist the relative path to each respondent's post questionnaire export as `post_survey_source_path` for quick audit replays.
- **Merging**: Left-join the engineered Stage 3 feature matrix onto `uv_stage1`, surface gaps in `results/uv_stage3_issues.csv`, and export the enriched UV to `results/uv_stage3.csv`.
- **Validation**: Confirm row counts, inspect category aggregates against raw composite scores, and document notable discrepancies in notebook markdown cells for transparency.
- **Outputs**: Save Stage 3 features and issues files with timestamp-safe fallbacks when filename collisions occur; this keeps the UV merge step aligned with the simplified three-stage pipeline.

## Best Practices
- Maintain helper dictionaries that translate raw stimulus names to canonical titles before populating the UV.
- Store intermediate mappings (e.g., `stimulus_rename`, `key_moments`) under `data/` and load them as reference tables when deriving new features.
- Keep transformation logic modular by encapsulating feature extraction steps into functions that take a respondent-level input and return a dictionary of UV-ready columns.
- Document any non-standard metrics inline with code comments or additional markdown cells in the notebook to support reproducibility.
- End every step where UV is updated with new data with a write to a .csv in the results folder

By following this methodology, teams can reliably fuse heterogeneous datasets into a single, analytics-friendly representation that scales across studies and clients.