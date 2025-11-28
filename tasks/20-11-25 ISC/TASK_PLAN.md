# Inter-Subject Correlation Task Plan

## Task Description
Develop `analysis/inter_subject_correlation.ipynb` to compute EEG inter-subject correlation (ISC) metrics from the raw 2 Hz PSD exports, aggregate pairwise synchrony across respondents, and produce analysis outputs that mirror the existing biometric workflow (Part 1 paired comparisons and Part 2 mixed models) alongside Short vs Long time-series visualisations.

## Numbered Plan
1. **Validate EEG Inputs and Metadata** – Inspect `data/Export` EEG sensor CSVs and `results/uv_stage1.csv` to confirm cadence, PSD band availability, stimulus naming alignment, and respondent coverage requirements for ISC.
2. **Reuse Time-Series Ingestion Scaffold** – Clone the loading/binning workflow from `analysis/time_series.ipynb` into the new notebook `analysis/inter_subject_correlation.ipynb`, parameterising it to extract 500 ms bins for EEG PSD metrics while caching per-respondent aligned series.
3. **Harmonise Exposure Windows per Pair** – For each title and format, derive the shared time span across respondents, trimming to the minimum overlapping duration and dropping incomplete 5-sample windows with 50 % overlap to preserve comparability.
4. **Compute Pairwise Sliding Correlations** – Implement reusable helpers that iterate respondent pairs, apply windowed Pearson correlations on each power band, and handle missing values via case-wise deletion.
5. **Aggregate ISC Across Pairs** – Collapse the pairwise outputs into aggregated time-series tables (mean, median, contributor counts) keyed by title, format, band, and window midpoint; persist results to `results/time_series_cache/` for plotting and downstream analysis.
6. **Mirror Overlay Visualisations** – Extend plotting utilities from `analysis/time_series.ipynb` to render Short vs Long ISC overlays per band/title, ensuring identical styling, legends, and export logic (PNG batches to `results/time_series_cache/plots`).
7. **Prepare Long-Form ISC Summaries** – Reshape aggregated ISC outputs into a tidy dataset (respondent pair × title × format × band) suitable for statistical testing, saving a canonical CSV akin to `uv_biometric_long.csv`.
8. **Replicate Biometric Analysis Structure** – Within `analysis/inter_subject_correlation.ipynb`, build Part 1 (paired comparisons) and Part 2 (title random-intercept mixed models) workflows for ISC, reusing helpers from `analysis/analysis_biometric.ipynb` to generate tables, plots, annotations, and one-line summaries per power band.
9. **Quality Checks and Documentation** – Spot-check correlation traces, validate statistic outputs against expectations, record assumptions/limitations in `tasks/20-11-25 ISC/` notes, and flag any data gaps or processing issues for follow-up.

## Next Phase: Notebook Implementation & Analysis
1. **Notebook Scaffold and Imports** *(completed)* – Instantiated `analysis/inter_subject_correlation.ipynb` with roadmap markdown, shared styling, PSD target column constants, and import configuration mirroring the time-series and biometric notebooks.
2. **Respondent-Level ISC Pipelines** *(in progress)* – Implement ingestion, binning, and window alignment cells that cache per-respondent PSD segments ready for sliding correlation at a confirmed 500 ms cadence.
3. **Pairwise Correlation Computation** *(not started)* – Add helpers to generate respondent-pair correlation matrices across sliding windows and log processing diagnostics.
4. **Aggregation and Visualisation** *(not started)* – Produce aggregated ISC tables, Short vs Long overlays, and exported plots using the shared formatting utilities.
5. **Statistical Analysis Outputs** *(not started)* – Reproduce Part 1/Part 2 summaries, tables, and plots for each power band within the notebook, saving tidy outputs for reporting.
6. **Validation and Documentation** *(not started)* – Summarise coverage checks, correlation sanity checks, and capture README-style notes alongside generated artefacts in `tasks/20-11-25 ISC/`.

- 2025-11-20: Drafted ISC task plan outlining ingestion, correlation, aggregation, visualisation, and analysis steps for the new notebook.
- 2025-11-21: Completed Step 1 – confirmed PSD band columns and 2 Hz cadence in EEG exports via `sensor_metadata.csv`, reviewed `uv_stage1.csv` respondent roster for stimulus assignments, and noted coverage caveats (marked "No EEG." respondents) for downstream filtering.
- 2025-11-21: Completed Step 2 – scaffolded `analysis/inter_subject_correlation.ipynb` with roadmap, imports, styling, PSD band constants, and window parameters ready for ISC processing.
- 2025-11-21: Confirmed PSD availability at a 500 ms cadence across Alpha/Beta/Delta/Gamma/Theta bands and queued ingestion updates to honour the slower sampling rate.
- 2025-11-21: Updated respondent-level pipeline to use `read_imotions` and trialled the first three respondents (104, 106, 116); all three lack PSD cluster columns, so no bins were generated yet (issues logged to `results/time_series_cache/isc_psd_issues.log`).
