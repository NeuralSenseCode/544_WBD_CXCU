# Biometrics & Self-Report Cross-Analysis Plan

## Task Description
Develop `analysis/analysis_cross.ipynb` to pair biometric metrics (FAC, GSR, ET, EEG) with Stage 2 self-report outcomes (Enjoyment NormalizedCorrected, Screening Familiarity C1, recall scores) and replicate the Hypothesis 3 three-part structure (overall, format-specific, title-level correlations) for each biometric × outcome combo, starting with FAC Adaptive Engagement and extending to the remaining sensors.

## Numbered Plan
1. **Confirm Inputs and Metrics** – Validate that `results/uv_biometric_long.csv`, `results/stage2_enjoyment_responses_long.csv`, and `results/post_study_survey_responses.csv` contain the required respondent IDs, title/form labels, and target columns (NormalizedCorrected enjoyment, Screening Familiarity C1, recall Q13/Q18 composites) with consistent naming.
2. **Notebook Scaffold & Shared Imports** – Create `analysis/analysis_cross.ipynb` with roadmap markdown, shared plotting defaults, and helper imports from `wbdlib` so the new notebook visually matches `analysis_self-report.ipynb` and `analysis_biometric.ipynb`.
3. **Build Master Merge Helpers** – Implement reusable loaders/joins that merge biometric stats with each self-report metric (enjoyment, familiarity, recall) by respondent/form/title while handling deduplication, filtering to target titles, and caching tidy long tables for repeated use.
4. **FAC Adaptive Engagement Pilot Module** – For FAC Adaptive Engagement **AUC only** (Mean is out of scope), implement Part 1 (overall correlations), Part 2 (Short vs Long slopes/plots), and Part 3 (title-level slopes/ANOVA) across enjoyment, familiarity, and recall to serve as the reference template.
5. **Extend Analysis to Remaining Biometrics** – Parameterise the pilot workflow so the requested metrics (FAC Contempt AUC, FAC Joy AUC, GSR Peaks Per Minute, ET Blink Rate, ET Fixation Dispersion Mean, EEG Distraction AUC) can run through the same Part 1–3 pipeline with minimal duplication, including automatic figure/table titles.
6. **Automate Plot/Table Exports** – Standardise annotation text, legends, and export logic (PNG + CSV summaries under `results/`) to keep outputs consistent with Hypothesis 3 reporting expectations.
7. **Interpretation & QA Notes** – Add verification cells that log coverage counts, missing data reasons, and notable findings per metric, then document these in `tasks/21-11-25 Biometrics and SR/` for downstream reporting.

## Progress Log
- 2025-11-21: Reviewed `analysis/analysis_self-report.ipynb` Hypothesis 3/E1 sections to capture the exact correlation, plotting, and annotation workflow that the new notebook must mirror.
- 2025-11-21: Inspected `stage2_enjoyment_responses_long.csv`, `post_study_survey_responses.csv`, and `uv_biometric_long.csv` to confirm the availability of Enjoyment NormalizedCorrected metrics, Screening Familiarity C1 fields, and FAC Adaptive Engagement stats aligned by respondent/form/title.
- 2025-11-21: Authored this task plan outlining the seven numbered steps and next actions for building `analysis/analysis_cross.ipynb`; next milestone is scaffolding the notebook and implementing the FAC Adaptive Engagement pilot module.
- 2025-11-24: Added the new `analysis_cross` notebook scaffold, configured shared plotting defaults, and implemented the reusable loader/merge helpers for enjoyment, familiarity, and recall data so Step 4 FAC Adaptive Engagement work can begin.
