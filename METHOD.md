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

### Stage 2 Sensor Feature Pipeline
- The helper trio `prepare_stimulus_segment`, `compute_sensor_features`, and `_trapezoid_integral` standardises windowing, metric calculation, and numerical integration (falling back to `np.trapz` when `numpy.trapezoid` is unavailable).
- `run_sensor_feature_pipeline(respondent_ids=None, export_label="uv_stage2_full", save_outputs=True)` orchestrates full-cohort processing: it validates mandatory columns per sensor modality, resolves EEG alias names (for example `Frontal Asymmetry Alpha`), applies key-moment clipping for long-form stimuli, and aggregates metrics following the UV naming convention.
- The function returns three DataFrames—`features_df`, `issues_df`, and the merged `uv` slice—and writes them to `results/` using safe timestamped fallbacks to avoid permission collisions (`*_features.csv`, `*_uv.csv`, `*_issues.csv`).
- Garbage collection (`gc.collect()`) after each respondent keeps memory usage stable when looping across dozens of large sensor files.
- Review the exported issues log before downstream modeling to reconcile missing sensors, unmapped stimuli, or empty windows.

## Best Practices
- Maintain helper dictionaries that translate raw stimulus names to canonical titles before populating the UV.
- Store intermediate mappings (e.g., `stimulus_rename`, `key_moments`) under `data/` and load them as reference tables when deriving new features.
- Keep transformation logic modular by encapsulating feature extraction steps into functions that take a respondent-level input and return a dictionary of UV-ready columns.
- Document any non-standard metrics inline with code comments or additional markdown cells in the notebook to support reproducibility.
- End every step where UV is updated with new data with a write to a .csv in the results folder

By following this methodology, teams can reliably fuse heterogeneous datasets into a single, analytics-friendly representation that scales across studies and clients.