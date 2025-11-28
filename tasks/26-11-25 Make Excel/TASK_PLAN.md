# Task Description
Document the workflow required to store the exact data behind every plot in `analysis_cross.ipynb`, `analysis_biometric.ipynb`, and `analysis_self-report.ipynb` as Excel files. Each Excel file must use the plot title for its filename and live in a new `results` subfolder. The exported tables must contain the same data powering the visualization (aggregated stats for summary charts, raw points for distributions) while reusing helpers from `analysis/wbdlib` wherever possible.

# Numbered Task Plan
1. **Confirm shared requirements and folder structure**
   - Re-read all notebooks to document the plotting stack, helper utilities in `analysis/wbdlib`, and how plot titles are produced.
   - Decide on the `results` subfolder name (e.g., `results/plot_data_exports/`) plus filename sanitizing and duplicate-handling rules.
   - Audit `wbdlib` for I/O helpers; if Excel support is missing, scope a reusable helper (e.g., `export_plot_source(df, title)`). Write down any helper changes before editing notebooks.

2. **analysis_cross.ipynb first-pass implementation**
   - Inventory every plotting cell, recording each figure title, the DataFrame powering it, and whether it visualizes aggregates or raw records.
   - For every plot, define the minimal dataset needed to regenerate the figure and how to derive it from existing intermediate frames.
   - Decide whether existing helpers already expose the right tables or whether to extend/add helpers in `wbdlib`; keep notebook code focused on calling helpers.
   - Plan where to call the export helper immediately after figure creation so exported data matches the chart exactly.
   - Outline validation steps (spot-check Excel vs. figure, ensure files land in the new folder, and verify naming parity with titles).

3. **analysis_biometric.ipynb alignment**
   - Repeat the inventory/derivation exercise notebook-wide, noting overlaps with `analysis_cross.ipynb` that can reuse helper logic.
   - Capture biometric-specific preprocessing steps (smoothing, normalization, per-channel averaging) that the exported data must reflect.
   - Extend the helper plan only when biometric charts need additional metadata (sampling rate, segment windows, participant counts) while remaining backward compatible.
   - Sequence retrofitting so sections sharing intermediate tables are handled together, reducing redundant computations and file writes.

4. **analysis_self-report.ipynb integration**
   - Catalog plots and their data requirements, emphasizing survey-derived metrics that may need cleaning/pivoting before export.
   - Verify whether self-report plots use unique helpers or transformations and plan how to reuse/extend them instead of duplicating logic.
   - Document additional validation (e.g., Likert ordering, label renames) required before saving Excel outputs so regenerated charts align with notebook visuals.

5. **Cross-notebook verification and documentation**
   - Define a smoke-test checklist covering folder creation, filename/title parity, aggregation level accuracy, and stale-file cleanup on reruns.
   - Plan documentation updates (README, MANUAL CORRECTIONS, or task notes) describing how to regenerate the Excel exports and where they reside.
   - Schedule a final clean run of all notebooks with export logic enabled, plus tests/spot-checks for any new helper functions.

## Step 2 Blueprint – analysis_cross.ipynb
### 2.1 Output scaffolding decisions
- Create `results/plot_data_exports/analysis_cross/` (later mirrored per notebook) with subfolders per part (`Part1_overall`, `Part2_format`, `Part2.1_title_format`, `Part3_title`) to keep the high file count organized.
- Implement `slugify_plot_title(title: str, suffix: str | None = None)` in `analysis/wbdlib/formatting.py` (or a new `naming.py`) to strip unsafe characters, collapse whitespace, and append stat/label suffixes for uniqueness.
- Extend `analysis/wbdlib/io.py` with `safe_write_excel` mirroring `safe_write_csv`: use `pd.ExcelWriter(engine="xlsxwriter")`, catch `PermissionError`, and fall back to a timestamped filename if the workbook is open.
- Standardize workbook layout: Sheet 1 = plotting data, Sheet 2 = derived stats (format summary, slopes, ANOVA), Sheet 3 = metadata (plot title, metric/outcome labels, filters). Scatter-only charts may skip Sheet 2.

### 2.2 Helper instrumentation strategy
- Add an optional `plot_exporter` callback parameter to `run_three_part_section` and `run_three_part_section2`; default to `None` to preserve current behavior.
- Part 1 scatter/regression: call the exporter before `plt.show()` with `subset` columns (`respondent`, `title`, `form`, `metric_value`, `outcome_value`) plus Pearson r, p, n, and mean stats for metadata.
- Part 2 format lmplots: export the `working` DataFrame plus `format_summary`, `slope_details`, and ANOVA frames. Title template `f"Part 2: {metric_axis} × Format ({outcome_label})"` should match the existing figure title/filename.
- Part 2.1 (title-by-title) inherits the same exporter call but suffix filenames with the title slug so each workbook stays unique.
- Part 3 title bars: export `title_corr_df` (Pearson r per title/form) and `title_diff_df` (Long vs Short interaction p) alongside Target Titles ordering metadata.
- Keep `THREE_PART_SUMMARY` logging intact; optionally have the exporter record the saved path for reconciliation.

### 2.3 Section coverage inventory
- Helper-driven sections already cover all metric × outcome combinations across FAC, GSR, ET, and EEG signals. Wiring the exporter into the helper automatically emits ~90 Excel files covering Parts 1–3.
- `run_three_part_section2` sections (ET Blink Rate and ET Fixation Dispersion) emit additional Part 2.1 plots; filenames must include both stat and title to avoid collisions.
- Manual FAC Adaptive Familiarity/Recall blocks build data frames inline. Either wrap them with the exporter directly or refactor into helper calls to keep outputs consistent.
- Regression diagnostics currently output only tables; future visuals can hook into the same exporter with their source DataFrames.
- Notebook summary export (`biometric_three_part_summary.csv`) should cross-reference the Excel paths from metadata sheets for traceability.

### 2.4 Data capture requirements for manual sections
- **FAC Adaptive × Familiarity**: export (a) each Part 1 `subset`, (b) Part 2 `working` + format/slope/ANOVA tables, (c) Part 3 `title_corr_df` + `title_diff_df`. Include the stat label in filenames.
- **FAC Adaptive × Recall**: same as above but add recall metric aliases (KM, Full, Composite) to filenames to distinguish multiple outputs from a single loop.
- **Future bespoke visuals** must supply the plotting DataFrame and metadata directly to the exporter to maintain parity across sections.

### 2.5 Validation checklist
- Dry-run with a filtered dataset (e.g., two titles) to confirm exporters fire, file counts match expectations, and workbook contents match charts.
- Rebuild a few plots from the exported Excel files in a scratch notebook to verify correlations/slopes align with notebook annotations.
- Confirm reruns overwrite unlocked files; if a file is open, `safe_write_excel` should timestamp the fallback filename and log it for awareness.

## Step 3 Blueprint – analysis_biometric.ipynb
### 3.1 Notebook-specific landscape
- Biometric notebook mixes multi-metric summary figures (heatmaps, layered scatter/regression, radar/parallel coordinates) and time-series comparisons per stimulus segment.
- Data sources include pre-computed summaries in `results/biometric_*` CSVs plus intermediate tables generated in the notebook (e.g., `metric_diff_df`, `per_title_summary`, `uv_biometric_long`). Each visualization’s exported data must mirror whichever representation reaches the plotting call.
- Plot titles usually include the biometric metric, cohort split (long vs short), and sometimes window/segment labels. Capture the exact string building logic to keep Excel filenames aligned.

### 3.2 Helper reuse and extensions
- Reuse `slugify_plot_title` and `safe_write_excel` from Step 2 to maintain consistent naming and error handling.
- Introduce a biometric-specific exporter wrapper (e.g., `export_biometric_plot(title, data_frames: dict, metadata: dict)`) that funnels through the generic helper but automatically stores files under `results/plot_data_exports/analysis_biometric/`.
- Where plots already call shared utilities (e.g., `run_metric_analysis`, `plot_title_compare`), add an optional `plot_exporter` parameter similar to Step 2 so instrumentation touches helpers, not dozens of notebook cells.
- For pure seaborn/matplotlib cells, add lightweight helper functions (e.g., `capture_metric_heatmap_source(df, title)`) to centralize data prep + export before plotting.

### 3.3 Section-by-section capture plan
- **Three-part summary equivalents**: Identify biometric sections mirroring the cross-notebook structure (metric vs outcome vs format). Feed the same `subset`, `format_summary`, and `title_corr_df` tables into the exporter so downstream analysts see identical schema.
- **Time-series overlays**: For rolling-average or segment-based plots, export the exact time-indexed DataFrame (columns: timestamp/segment, metric value per cohort) plus metadata describing smoothing window, sampling rate, and filters applied.
- **Heatmaps / correlation matrices**: Export the pivot table or correlation matrix feeding `sns.heatmap` before transformation. Include ordering vectors (metric sort order, title order) in the metadata sheet so re-plotting maintains the original structure.
- **Per-title radar/parallel plots**: When the notebook iterates through titles, ensure each iteration writes a workbook with the per-metric vectors plus the aggregated stats driving the polygon. Append the title slug to filenames.
- **Significance annotation tables**: Many plots overlay p-values or significance stars from separate tables. Include those tables either as a second sheet or in metadata to keep the Excel output self-sufficient.

### 3.4 Data fidelity considerations
- Respect any smoothing, z-scoring, or baseline subtraction happening between source CSVs and plotted DataFrames; exports must reflect post-processing results, not raw signals.
- Capture participant/sample counts when filtering (e.g., dropping low-quality sensors) and note them in metadata for reproducibility.
- Where multiple metrics share a combined figure, store each metric’s data either on separate sheets or with a `metric` column to avoid ambiguity.
- Confirm privacy constraints: if any biometric plots aggregate at per-respondent resolution, ensure exported tables abide by the project’s anonymization rules (e.g., hashed IDs already in use).

### 3.5 Validation checklist
- Run the notebook with exporters enabled for a limited subset (one stimulus) to confirm runtime impact and file counts.
- Spot-check a time-series export by regenerating the overlay from Excel to ensure smoothing windows and annotations match.
- Verify that helper-driven exports (e.g., via `run_metric_analysis`) behave identically whether invoked from cross or biometric notebooks by sharing the same core helper implementation.

# Progress
- **Step 1** (26 Nov 2025): Requirements review complete; recorded need for sanitized plot-title filenames, new `results` subfolder, and helper reuse/extension plan.
- **Step 2** (27 Nov 2025): analysis_cross now calls the shared exporter everywhere scatter, lmplot, and title-level bar charts are produced. Filenames are normalized via `_normalize_export_title`, and every workbook lands in `results/plot_data_exports/analysis_cross/` with companion metadata sheets.
- **Step 3** (27 Nov 2025): analysis_biometric wired into the same exporter stack through `_export_metric_bundle`, ensuring `{sensor} – {metric}` titles and Excel names stay in sync across heatmaps and regression sections.
- **Step 4** (27 Nov 2025): analysis_self-report instrumentation underway. Hypothesis 1 plus the Hypothesis 2 open-ended KMS sections now export their plotting frames and summary tables with sanitized titles; remaining Hypothesis 2 subsections, Hypotheses 3–4, and exploratory blocks still need exporter coverage.
