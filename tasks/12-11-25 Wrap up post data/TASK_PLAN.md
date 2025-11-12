# Task: Wrap up post-study survey data handoff

Prepare the client-facing exports and documentation that surface every post-study survey response with the associated scoring context. When this plan refers to a "long-form" table it means the long-format (tidy) layout where each row captures a single respondent-question response—not the long-form stimulus cut.

## Detailed Plan

1. **Audit current assets and lock the schema**
   - Review existing notebooks/exports (`results/uv_open_ended_long_recall.csv`, `results/uv_open_ended_long.csv`, Stage 3 tables, raw `data/Post/` files) to inventory available columns.
   - Draft the unified long-format schema for `post_study_survey_responses.csv`, incorporating respondent metadata plus the full `post_survey_map.csv` metadata. *Milestone: agreed schema checklist.*
2. **Engineer the extraction approach**
   - Build a dedicated client-deliverables helper stack in `analysis/assemble_uv.ipynb` (new functions: `load_post_survey_raw`, `reshape_post_survey_long`, `attach_post_metadata`, `append_post_scores`) rather than modifying Stage 4, preserving the existing open-ended pipeline.
   - Document normalization rules—coerce respondent IDs to zero-padded strings, trim whitespace, standardize timestamps, harmonize `form`/`format` labels, and map titles through Stage 1 lookup (`Short Form`/`Long Form`).
   - Define join strategy: long-form responses keyed on (`respondent`, `question_code`) joined with `post_survey_map` metadata, Stage 1 demographics for group/form context, Stage 3 recognition melt for binary/likert scores, and Stage 5 recall outputs for LLM-derived scores. *Milestone: finalized extraction design documented in notebook comments or markdown.*
3. **Build the long-format dataset**
   - Implement the logic that compiles every respondent-question response with provenance columns (`respondent`, `group`, `form`, `title`, `question_code`, `questionnaire`, `source_path`) and attaches metadata fields.
   - Integrate existing recognition metrics and Stage 5 recall LLM outputs without re-running the scorer, mapping them into `score_value`, `score_confidence`, `score_method`, and `score_explanation`; clearly flag questions without scores. *Milestone: first draft `post_study_survey_responses.csv` written to `results/`.*
4. **Validate and document**
   - Run audits on row counts, uniqueness, metadata completeness, and spot-check against raw CSVs.
   - Draft the client README describing each column, definitions of `type`, `subscale`, `category`, `accuracy`, and current scoring coverage (recognition + recall LLM). *Milestone: validated dataset plus README ready for review.*
5. **QA, delivery, and follow-ups**
   - Peer-review both artifacts, finalize file locations, and log paths in `PROGRESS.md`.
   - Record outstanding scoring work or open questions in `MANUAL CORRECTIONS AND OBSERVATIONS.md` (or equivalent). *Milestone: deliverables approved and next actions captured.*

## Progress
- 2025-11-12: Step 1 complete. Inventoried existing post questionnaire assets (`results/uv_open_ended_long_recall.csv`, `results/uv_open_ended_long.csv`, Stage 3 recognition outputs, raw `data/Post/` exports) and drafted the target `post_study_survey_responses.csv` schema: `submitted_timestamp`, `respondent`, `group`, `questionnaire`, `question_code`, `question_text`, `question_type`, `subscale`, `category`, `accuracy`, `stimulus_form`, `stimulus_title`, `response_raw`, `response_clean`, `response_numeric`, `score_value`, `score_confidence`, `score_method`, `score_explanation`, `source_path`, with `score_value` earmarked to carry recognition stats or existing LLM recall scores.
- 2025-11-12: Step 2 complete. Selected a dedicated client-deliverables pipeline, outlined helper functions, normalization rules (ID coercion, timestamp parsing, whitespace trimming, form/title harmonization), and joins to `post_survey_map`, Stage 1 exposure titles, melted Stage 3 recognition metrics, and Stage 5 recall outputs so scoring columns reuse existing values without re-running the LLM.
- 2025-11-16: Step 3 complete. Added the helper stack and assembly routine to `analysis/assemble_uv.ipynb`, generated the tidy table (now 6,059 rows after timestamp-based deduplication), and exported `results/post_study_survey_responses.csv`; remaining follow-up is to audit `metadata_issues_df` and describe column behaviors in the README.
- 2025-11-16: Step 4 complete. Validation summary (Cell 63) confirms 6,059 rows, 83 respondents, and 1,775 scored responses; timestamp deduplication removed 73 older submissions and README updated to document the change and remaining recognition-form gaps (~1,158 entries in `metadata_issues_df`).
- 2025-11-16: Step 5 complete. QA review accepted the CSV/README, duplicates resolved, outstanding recognition-form follow-up logged for future work, and deliverables ready for handoff.
