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
{form}_{title}_{sensor_type}_{metric}_{method}
```

Where:
- `form` describes the presentation format (for example `Long`, `Short`, `Baseline`).
- `title` identifies the stimulus or survey construct. Use lowercase and separate words with spaces, camelCase, or hyphens rather than underscores (e.g., `mad max fury road`).
- `sensor_type` indicates the modality, such as `EEG`, `GSR`, `ET`, `FAC`, `Survey`, or `Demo`.
- `metric` captures the core signal dimension (e.g., `Engagement`, `PeakCount`).
- `method` records the statistical operation applied (e.g., `Mean`, `Max`, `AUC`).

Use underscores *only* to separate the major segments shown above (`form_title_sensor_type_metric_method`). Within any single segment employ spaces, camelCase, or hyphens to maintain readability (for example `long_mad max fury road_EEG_Engagement_Mean`).

## Data Preparation Workflow
1. **Renaming/ casting stimuli**: Give stimuli new names 
2. **Define key files**: Provide a detailed description of key files used
3. **Define any data structure**: Provide detail on ways in which data may be uniquely structured. iMotions headers etc.



## Data Integration Workflow
1. **Initialize UV**: Create an empty DataFrame with the baseline columns. Populate respondent metadata from roster files or enrollment logs.
2. **Sensor ingestion**: Read raw exports using standardized readers (for example, `read_imotions`). Extract per-respondent, per-stimulus summaries and append as new columns following the naming convention.
3. **Survey merge**: Process self-report instruments, ensuring respondent identifiers align with the UV. Add each metric as a new column with `sensor_type` set to `Survey` or another appropriate label.
4. **Demographics and external data**: Join any additional contextual features (e.g., media familiarity scores, psychometrics). Prefix columns with `demo_` or another agreed tag for clarity.
5. **Validation**: After each integration step, confirm row counts, respondent coverage, and absence of duplicated identifiers. Document any exclusion criteria or imputations.
6. **Versioning**: Save periodic snapshots (CSV or Parquet) to the `results/` directory with timestamped filenames to preserve provenance while iterating.

## Best Practices
- Maintain helper dictionaries that translate raw stimulus names to canonical titles before populating the UV.
- Store intermediate mappings (e.g., `stimulus_rename`, `key_moments`) under `data/` and load them as reference tables when deriving new features.
- Keep transformation logic modular by encapsulating feature extraction steps into functions that take a respondent-level input and return a dictionary of UV-ready columns.
- Document any non-standard metrics inline with code comments or additional markdown cells in the notebook to support reproducibility.
- End every step where UV is updated with new data with a write to a .csv in the results folder

By following this methodology, teams can reliably fuse heterogeneous datasets into a single, analytics-friendly representation that scales across studies and clients.