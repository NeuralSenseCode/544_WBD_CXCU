# Stage 5.2 Key Moment Recall Workflow

This document serves as a standalone brief for the Stage 5.2 recall-scoring track. Stage 5.2 extends the existing recall pipeline (now Stage 5.1) by introducing a key-moment-only evaluation for respondents who viewed the long-form content. The goal is to quantify whether long-form viewers retained the specific key moment highlighted in the short-form clips, enabling apples-to-apples comparisons with respondents who only saw the short form.

## Objectives
- Deliver a second recall-scoring export—`recall_coded_responses_key_moment.csv`—that measures key-moment recall across both long- and short-form respondents.
- Preserve the original Stage 5.1 (full-segment) scoring, now renamed to Stage 5.1, with outputs promoted to `recall_coded_responses_full.csv`.
- Integrate both recall perspectives into the unified view (UV) so downstream analyses can switch between full recall and key-moment recall metrics.

## Inputs
- `results/uv_open_ended_long_recall.csv`: respondent-level free-text recall responses used by both Stage 5.1 and Stage 5.2.
- `data/model_answers_events.md`: canonical event lists for each title and form. Stage 5.2 will exclusively reference the short-form (key moment) event lists when scoring long-form respondents.

## Outputs
- `results/recall_coded_responses_full.csv`: Stage 5.1 output (full segment recall). This file replaces the prior `recall_coded_responses.csv` reference.
- `results/recall_coded_responses_key_moment.csv`: Stage 5.2 output (key-moment recall). Long-form respondents are graded against short-form key-moment answers; short-form respondents retain their original mapping.
- UV columns:
   - Stage 5.1: `{Form}_{Title}_Post_Recall_OpenEndedSum`.
   - Stage 5.2: `{Form}_{Title}_Post_Recall_OpenEndedKMS` (Key Moment Score).

## Scoring Logic Summary
- **Short-form respondents:** identical treatment in Stage 5.1 and Stage 5.2. Responses are compared against the short-form (key moment) model answers.
- **Long-form respondents:**
   - Stage 5.1 evaluates the entire long-form event list.
   - Stage 5.2 evaluates only the key-moment events; recollection of non-key-moment content is ignored. Respondents recalling none of the key-moment events receive a score of 0, while accurately recalling only the key moment yields a perfect score.
- Both stages run through the same LLM-assisted scoring harness, but Stage 5.2 swaps the event reference set during scoring for long-form viewers and, after each batch, re-runs any missing rows individually before logging unresolved cases to `results/recall_coded_responses_key_moment_errors.csv`.

## Work Breakdown
1. Confirm the current Stage 5.1 flow: locate notebook cells, exported filenames (`recall_coded_responses_full.csv`), UV merge references, and mentions in `PROGRESS.md`, `SCORING.md`, `ANALYSIS PROGRESS.md`.
2. Recast Stage 5 as Stage 5.1 everywhere: update headings/text, rename outputs to `recall_coded_responses_full.csv`, and ensure the UV merge still pivots to `{Form}_{Title}_Post_Recall_OpenEndedSum`.
3. Stage 5.2 development and validation:
    - 3.1 Create `recall_openended/key moment/method2_keymoment_pilot.ipynb` using the Stage 5.1 logic as a template. Force long-form respondents to use the short-form event lists within the scoring prompt and payload.
    - 3.2 Surface the revised LLM prompt/instructions for manual review before executing any token-consuming cells.
    - 3.3 Pilot the Stage 5.2 workflow on six randomly selected Abbott Elementary responses (three long-form, three short-form) to validate the new scoring behavior.
    - 3.4 Review pilot outputs with the user; iterate on prompt wording or scoring logic as needed until the key-moment scoring meets expectations.
   - 3.5 ✅ (2025-11-11) Finalized Stage 5.2 implementation merged into `analysis/assemble_uv.ipynb` with shared helper functions.
   - 3.6 Before running the full Stage 5.2 batch (which will incur LLM costs), obtain explicit user approval and then generate the production `recall_coded_responses_key_moment.csv` file.
4. ✅ (2025-11-11) Extend the UV merge section so both Stage 5.1 and Stage 5.2 exports are ingested, emitting `{Form}_{Title}_Post_Recall_OpenEndedKMS` alongside the existing Stage 5.1 sums.
5. ✅ (2025-11-11) Update supporting documentation (`PROGRESS.md`, `SCORING.md`, `ANALYSIS PROGRESS.md`, notebook markdown cells) to capture the new stage naming, inputs, outputs, and approval checkpoints.

## Review Gates and Approvals
- **Prompt Approval:** User signs off on the revised Stage 5.2 prompt prior to any LLM execution.
- **Pilot Approval:** Pilot outputs (six Abbott Elementary responses) reviewed and approved before promoting changes to the full pipeline.
- **Production Run Approval:** User authorizes the full Stage 5.2 execution after the code is merged back into `analysis/assemble_uv.ipynb`.

## Outstanding Questions / Assumptions
- Abbott Elementary is the initial pilot title; confirm whether additional titles require pilot validation before the full run.
- Confirm whether the Stage 5.2 scoring should output additional diagnostics (for example, per-event match flags) beyond the current Stage 5.1 schema.
- Validate that the existing environment/API keys support the additional LLM usage expected for the Stage 5.2 run.
