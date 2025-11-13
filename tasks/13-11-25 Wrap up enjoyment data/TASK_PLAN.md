# Task: Wrap up Stage 2 survey data handoff

Prepare the client-facing exports and documentation that surface every Stage 2 enjoyment survey response with the associated scoring metadata. “Long-form” refers to tidy long tables where each row represents a single respondent–question response.

## Detailed Plan

1. **Audit current Stage 2 assets and confirm schema**
   - Review existing notebooks/exports (`analysis/assemble_uv.ipynb`, `results/uv_stage2.csv`, `results/uv_stage2_open_ended.csv`, `results/uv_stage2_features.csv`, `results/uv_stage2_issues.csv`) and raw survey sources (MERGED survey TSVs in `data/Post/` archives) to inventory available columns and note respondent coverage gaps (e.g., respondent `35`).
   - Draft the unified long-format schema for the Stage 2 enjoyment export, incorporating respondent metadata, item attributes, and scoring columns aligned with Stage 2 composite metrics. Capture dependencies on Stage 1 demographic tables and `survey_column_rename.csv`.
   - **Milestone:** Agreed schema checklist captured in notebook markdown or the task folder.

2. **Engineer the extraction approach**
   - Specify helper usage within `analysis/assemble_uv.ipynb` Stage 2 block, leveraging `wbdlib.survey` and related utilities. Outline any new helper signatures (e.g., `load_stage2_survey_raw`, `reshape_stage2_long`, `attach_stage2_metadata`, `append_stage2_scores`) before implementation.
   - Document normalization rules—coerce respondent IDs to zero-padded strings, trim whitespace, standardize timestamps, harmonize form/title labels via Stage 1 lookups, and ensure question codes align with `survey_columns_by_group.csv` mappings.
   - Define join strategy: long-form responses keyed on (`respondent`, `question_code`, `stimulus_title`) enriched with rename-map metadata, Stage 1 demographics, Stage 2 composite scores, and sentiment/open-ended outputs without re-running scorers.
   - **Milestone:** Finalized extraction design recorded in notebook comments or supporting markdown.

3. **Build the Stage 2 long-format dataset**
   - Implement the pipeline that compiles every respondent-question response with provenance columns (`submitted_timestamp`, `respondent`, `group`, `stimulus_form`, `stimulus_title`, `question_code`, `questionnaire`, `source_path`) and attaches metadata fields (`question_text`, `question_type`, `subscale`, `category`, `accuracy`).
   - Integrate existing composite/likert metrics and sentiment outputs into scoring fields (`score_value`, `score_confidence`, `score_method`, `score_explanation`), clearly flagging unanswered or unscored items. Ensure respondent duplicates are resolved using timestamp dedupe rules established in Stage 2 ETL.
   - Write the resulting CSV to `results/` (target filename `tasks/13-11-25 Wrap up enjoyment data/enjoyment_responses_long.csv`) and persist intermediate diagnostics (e.g., `metadata_issues_df`).
   - **Milestone:** First draft long-format CSV exported to `results/`.

4. **Validate and document deliverables**
   - Run audits covering row counts, uniqueness keys, metadata completeness, and sampling spot-checks back to raw MERGED TSVs. Reconcile counts with `uv_stage2.csv` aggregates and log unresolved gaps (e.g., missing respondent forms).
   - Draft/update the client README describing each column, subscale definitions, scoring coverage, and any outstanding data caveats or missing respondents. Include guidance on interpreting Stage 2 composite scores vs. raw item responses. Output this README to `tasks/13-11-25 Wrap up enjoyment data/enjoyment_responses_long_README.csv`
   - **Milestone:** Validated dataset and README ready for internal review.

5. **QA, delivery, and follow-ups**
   - Peer-review both artifacts, confirm final filenames/locations, and capture completed deliverables plus validation notes in `PROGRESS.md`.
   - Record outstanding issues (e.g., absent MERGED survey TSV copies, respondent `35` coverage) in `MANUAL CORRECTIONS AND OBSERVATIONS.md` and surface any requests for additional data pulls.
   - **Milestone:** Deliverables approved for handoff and next actions logged.

## Progress

- 2025-11-13: Drafted task plan; awaiting kickoff of Step 1.
- 2025-11-13: Step 1 in progress — reviewing Stage 2 assets (`assemble_uv.ipynb`, `uv_stage2*.csv`, rename maps) and confirming availability of MERGED survey TSVs; documenting schema considerations.
- 2025-11-13: Step 1 milestone met — schema checklist captured in `tasks/13-11-25 Wrap up enjoyment data/stage2_schema_checklist.md`; noted missing MERGED TSVs and respondent `35` gap for follow-up.
- 2025-11-13: Step 2 milestone met — extraction design captured in `tasks/13-11-25 Wrap up enjoyment data/stage2_extraction_design.md`; helper signatures, normalization rules, join strategy documented for notebook implementation.
- 2025-11-13: Step 3 milestone met — Stage 2 long-form export built in `analysis/assemble_uv.ipynb` and saved to `results/stage2_enjoyment_responses_long.csv`; preview written to task folder.
- 2025-11-13: Step 4 milestone met — validation summary exported and README drafted at `tasks/13-11-25 Wrap up enjoyment data/enjoyment_responses_long_README.md`.
