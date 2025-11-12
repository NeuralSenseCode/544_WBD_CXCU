Task Description:
Replicate "Exploratory Analysis 1 – Enjoyment and Recall" as "Exploratory Analysis 1 – Enjoyment and Open Ended Recall" by swapping the recognition-based recall metrics for the KMS open-ended recall values, mirroring the workflow already adapted for Hypothesis 4.

Plan:
1. Audit the existing Exploratory Analysis 1 pipeline to document inputs, helper functions, and reporting structure, and confirm availability of the KMS recall fields used in the H4 adaptation.
2. Part 1 Completion: Construct the merged enjoyment + KMS recall dataset, rerun the overall correlation and visual outputs, and update labels/titles to the new analysis name.
3. Part 2 Completion: Reproduce the format-specific (Long vs Short) correlations and plots using the KMS recall data, ensuring statistical tests match the prior pattern.
4. Part 3 Completion: Refresh the title-level correlation analyses with the KMS recall metrics, including regression slopes, annotations, and supporting tables.
5. Part 4 Completion: Generate the title-by-format comparison visuals and summaries with KMS recall values, retaining significance callouts and commentary alignment.
6. Validate all outputs (figures, tables, narrative cells), update analysis notes/logs, and queue any follow-up tasks for documentation or review.

Progress:
- 2025-11-12: Step 1 complete. Documented the current E1 workflow (merging `enjoyment_long` with `recognition_long` for `e1_base`) and confirmed the H4 KMS stack (`open_recall_long_kms`, `h4_kms_base`, downstream correlation tables) exposes parallel helpers/structures for re-use.
- 2025-11-12: Step 2 complete. Built the new E1 KMS base table by merging enjoyment composites with `open_recall_long_kms`, confirmed record counts by form/title, and reran the overall correlation plot/table with updated labels.
- 2025-11-12: Step 3 complete. Reproduced the format-level correlations/plots using the KMS data, captured slope-difference stats via `format_model_kms`, and refreshed the annotations to match the new analysis name.
- 2025-11-12: Step 4 complete. Rebuilt the title-level correlations, slope comparisons, and table outputs with KMS recall metrics, ensuring visuals and summaries mirror the original Part 3 workflow.
- 2025-11-12: Step 5 complete. Delivered the title-by-format comparison bars with KMS correlations, including significance brackets, table exports, and refreshed narrative summaries for Part 4.
- 2025-11-12: Step 6 complete. Validated all E1 KMS cells execute without errors, spot-checked figures/tables, and flagged the analysis log for documentation follow-up.
