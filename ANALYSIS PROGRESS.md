# Analysis Progress Log

- 2025-11-04: Initialized analysis log. Loaded `results/uv_merged.csv` within `analysis/analysis_self-report.ipynb` and produced a column-to-category overview at `results/uv_column_categories.csv` for upcoming hypothesis workflows.
- 2025-11-04: Reformatted `results/uv_column_categories.csv` to contain explicit `header` and `category` columns for easier filtering in later stages.
- 2025-11-04: Began H1 analysis; created tidy enjoyment dataset, generated within-subject paired t-tests with visualisations, and ran title-level mixed models for `EnjoymentComposite_Normalised` variants.
- 2025-11-04: Extended H1 Part 2 checks to include `EnjoymentComposite_Sum` and `EnjoymentComposite_Corrected`, confirming mixed-model directionality across raw composites.
- 2025-11-04: Added `EnjoymentComposite_Mean` to both within-subject and mixed-model runs to compare scaling differences across composites.
- 2025-11-04: Refined Part 1 visuals to focus on normalized composites (`EnjoymentComposite_Normalized` and `_NormalizedCorrected`) so plots align with per-item scaling, removing `_Sum` and `_Corrected` variants.
- 2025-11-04: Introduced normalized subscale analyses plus title-level mixed models, and added a subscale item-count inventory to explain discrepancies between normalized and summed composites.
- 2025-11-04: Opened H2 workflow focusing on post-recognition composites; normalised `Long_key_Post_Recognition_Mean`/`Short_key_Post_Recognition_Mean`, re-used the paired one-tailed t-test with box+swarm and companion mean bar plots, and recorded summary tables for the within-subject comparison.
- 2025-11-04: Extended H2 Part 2 to the title level, mapping normalised key composites onto the three target titles, fitting a mixed-effects model with title random intercept, and rendering both distribution and mean bar charts with annotated effects (`coef≈0.084`, `p_one-tailed≈0.0035`).
- 2025-11-04: Completed H2 Part 3 by normalising the broader recognition categories, reversing the Long Unseen/Unseen scales, and plotting mean bars with SEM overlays for comparison across question types.
- 2025-11-04: Built out H3 Parts 1–3: merged normalised familiarity and enjoyment composites, produced overall and format-split correlations, and added interaction-based slope-difference tests and annotations for the three target titles.
- 2025-11-04: Added H3 Part 4 composite bar chart contrasting Long vs Short correlations per title, including significance asterisk annotations and a legend note detailing the asterisk thresholds after repositioning the legend beneath the figure.
- 2025-11-04: Created H4 section pairing normalised familiarity with post-recognition scores; replicated the four-part workflow (overall, format split, title split, and title-format comparison) with updated slope tests and correlation callouts.
- 2025-11-04: Added Exploratory Analysis 1 (Enjoyment vs Recall) mirroring the H3/H4 structure by merging enjoyment composites with recall metrics and producing the same four-part correlation suite.
- 2025-11-04: Extended H2 Part 2 with separate title-level models and visuals for the binary recognition hits and the confidence multipliers, mirroring the composite plots while reporting their mixed-model coefficients and summaries.
- 2025-11-05: Refined H2 Part 2a/2b binary recognition reporting so the notebook now prints per-title tables and one-liners with sample counts, one-tailed proportion z-tests (with Welch fallback), and references to the overall mixed-model p-value.
