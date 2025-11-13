Task Description:
Coordinate the creation of a new biometric analysis notebook (`analysis/analysis_biometric.ipynb`) that mirrors the structure and analytical approach of Hypothesis 1 in `analysis/analysis_self-report.ipynb`, using `results/uv_biometric_full.csv` as the data source and focusing on Mad Max, The Town, and Abbott Elementary.

Numbered Task Plan:
1. Review reference materials: `analysis/analysis_self-report.ipynb`, `ANALYSIS PROGRESS.md`, `SCORING.md`, and any relevant notes in `MANUAL CORRECTIONS AND OBSERVATIONS.md` to confirm expected structure, styling, and reporting conventions.
2. Inspect `results/uv_biometric_full.csv` to verify column naming patterns (`{form}_{title}_{sensor}_{metric}_{stat}`), confirm availability of Mad Max, The Town, and Abbott Elementary entries, and document all sensors, metrics, and stats present.
3. Draft the notebook outline replicating `analysis_self-report.ipynb`: introduction, Data Setup (library imports, constants, utility functions), early title normalization (e.g., correcting `Abbot` → `Abbott`), data loading, filtering to target titles and the four focal sensors (EEG, ET, FAC, GSR), plus creation of helper columns (e.g., respondent identifiers, form labels) required for within-subject and mixed-effects analyses.
4. Implement reusable data preparation helpers to reshape the biometric dataset per sensor and metric (long-form tables containing respondent, title, form, metric value, and stat type) while preserving consistency with prior notebook conventions, prioritising existing utilities from `analysis/wbdlib`; introduce or modify helpers in that library only when strictly necessary and backed by docstrings.
5. Audit `{form}_{title}_duration` fields in `results/uv_biometric_full.csv` to confirm Long and Short segments differ by no more than 1–2 seconds per title, ensuring comparable measurement windows once the notebook structure is in place.
6. For each sensor, create a dedicated section in the notebook with subsections per metric, matching heading levels, markdown styling, and color palettes used previously.
7. Within each sensor-metric subsection Part 1, compute respondent-level averages across Long and Short forms for every stat, derive Long–Short differences, perform one-tailed paired t-tests (expecting Long > Short), and render tables plus narrative summaries (means, t statistics, p-values) in the established format.
8. Within each sensor-metric subsection Part 2, fit mixed-effects models (`title` as random intercept, `form_long` as fixed effect) using the reshaped data, extract coefficient estimates and confidence intervals, and replicate the model summary presentation style from Hypothesis 1, including text interpretation.
9. Generate visualizations for both Parts: paired plots for within-subject comparisons and title-level distributions with overlaid model predictions, ensuring the aesthetics (fonts, sizing, color schemes) match `analysis_self-report.ipynb` outputs.
10. Compile section-level summary statements that highlight mean Long and Short values (no normalized percentages), key statistical outcomes, and any notable sensor-specific insights, mirroring the one-liner structure from the reference notebook.
11. Validate notebook reproducibility by running all cells sequentially, resolving warnings or errors, and documenting any limitations or follow-ups in `tasks/13-11-25 Biometric KM analysis` for future reference.

Notebook Outline (Step 3 Draft):
1. Markdown title and introduction summarising biometric hypothesis focus and referencing EEG, ET, FAC, and GSR sensors.
2. Markdown recap of workflow mirroring Hypothesis 1 structure (Part 1 within-subject t-tests, Part 2 mixed models) and explicitly stating expectation of Long > Short.
3. Data Setup section:
	- Python imports (pandas, numpy, seaborn, matplotlib, statsmodels, scipy) plus existing helpers from `analysis/wbdlib` such as `COLOR_MAP`, `register_boxplot_with_means`, `one_tailed_p_from_paired_t`, `print_long_short_summary`, `format_p_value`, and plotting utilities.
	- Project constants (`PROJECT_ROOT`, `RAW_PATH`) and consistent styling config (fonts, palette) aligned with `analysis_self-report.ipynb`.
4. Data loading and normalization:
	- Load `results/uv_biometric_full.csv` into `uv_biometric`.
	- Immediately standardise title spellings with a regex replace for `Abbot` → `Abbott` across columns and object data, leveraging existing helper patterns.
	- Identify respondent identifier column (`respondent_id`) and filter rows to Mad Max, The Town, and Abbott Elementary based on the cleaned titles.
5. Column shaping utilities:
	- Reuse or wrap existing `wbdlib` helpers to parse `{form}_{title}_{sensor}_{metric}_{stat}` column names.
	- Restrict to the four target sensors and create tidy long-form tables capturing `respondent_id`, `title`, `form`, `sensor`, `metric`, `stat`, and `value`.
	- Persist reusable mappings (e.g., sensor → metrics list, metric labels) to avoid recomputation across sections.
6. Exploratory summary tables (optional quick checks) showing record counts by sensor/metric/form for sanity, styled like the reference notebook.
7. Per-sensor sections (EEG, ET, FAC, GSR):
	- Markdown heading introducing the sensor and listing included metrics.
	- For each metric subsection:
	  * Markdown blurb describing metric definition and stats available.
	  * Part 1 code cell computing respondent-level means, Long–Short differences, paired one-tailed t-tests, formatted summary table (`to_percent_table` style but reporting raw means), and one-liner narrative via `print_long_short_summary` (without percent conversions).
	  * Part 1 visualisation mirroring Hypothesis 1 (paired plot/boxplot) using shared colour palette.
	  * Part 2 code cell constructing dataset for mixed-effects model (`form_long`, `title` random intercept), fitting via `statsmodels` in the same pattern as Hypothesis 1, and printing model summary with formatted coefficients and confidence intervals.
	  * Part 2 visual showing per-title distributions with overlaid model lift annotation.
8. Sensor-level wrap-up markdown summarising key findings (mean Long vs Short values, statistical significance) without normalised percentages.
9. Final aggregated conclusion section synthesising outcomes across sensors, highlighting where Long significantly exceeds Short, and noting any data limitations.

Sensor Section Blueprint (Step 6 Preparation):
- EEG: Distraction (Mean, AUC), Drowsy (Mean, AUC), FrontalAlphaAsymmetry (Mean, AUC), HighEngagement (Mean, AUC), LowEngagement (Mean, AUC), Workload (Mean, AUC).
- ET: Blink (Count, Rate), Fixation (Count, PerMinute), FixationDispersion (Mean), FixationDuration (Mean).
- FAC: AdaptiveEngagement (Mean, AUC), Anger/Confusion/Contempt/Disgust/Engagement/Fear/Joy/Neutral/Sadness/Sentimentality/Surprise (Mean, AUC, Binary), PositiveAdaptiveValence/NegativeAdaptiveValence/NeutralAdaptiveValence (Mean, AUC).
- GSR: PeakDetected (Binary), Peaks (Count, PerMinute).

Progress:
- 2025-11-13: Completed Step 1 by reviewing `analysis/analysis_self-report.ipynb`, `ANALYSIS PROGRESS.md`, `SCORING.md`, and pertinent notes in `MANUAL CORRECTIONS AND OBSERVATIONS.md` to confirm reporting structure and styling conventions for the biometric notebook.
- 2025-11-13: Completed Step 2 by profiling `results/uv_biometric_full.csv`; confirmed `{form}_{title}_{sensor}_{metric}_{stat}` naming (with 7 sensors, 39 metrics, 81 stats), verified presence of Mad Max, The Town, and Abbott Elementary title subsets, and noted ancillary columns (`source_file_x`, demographics, etc.) outside the pattern for potential exclusion.
- 2025-11-13: Completed Step 3 by drafting the biometric notebook outline—mirroring Hypothesis 1 structure, front-loading `Abbot` → `Abbott` normalization, and constraining analysis flow to EEG, ET, FAC, and GSR sensor families.
- 2025-11-13: Completed Step 4 by introducing reusable helpers in `analysis/wbdlib/biometric.py` for parsing headers, reshaping to tidy form, summarising coverage, and auditing duration gaps; exposed them via `wbdlib.__init__` for notebook use.
- 2025-11-13: Completed Step 5 by auditing `{form}_{title}_duration` columns through `wbdlib.get_duration_differences`; confirmed Long vs Short windows differ by ≤1.48s (Mad Max ≈1.48s, The Town ≈1.20s, Abbott Elementary ≈0.47s), satisfying the comparability check.
- 2025-11-13: Completed Step 6 by inventorying EEG/ET/FAC/GSR metric-stat combinations for target titles and drafting per-sensor section blueprints to mirror Hypothesis 1 structure in the forthcoming notebook.
- 2025-11-13: Completed Step 5 by auditing `{form}_{title}_duration` columns through `wbdlib.get_duration_differences`; confirmed Long vs Short windows differ by ≤1.48s (Mad Max ≈1.48s, The Town ≈1.20s, Abbott Elementary ≈0.47s), satisfying the comparability check.
