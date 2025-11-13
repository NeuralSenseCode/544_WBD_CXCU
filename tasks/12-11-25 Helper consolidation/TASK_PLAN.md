# Task: Consolidate assemble_uv helpers into wbdlib

Refactor the Stage 2–5 helper stack inside `analysis/assemble_uv.ipynb` so that recurring utilities live in the shared `wbdlib` package. The goal is to make the notebook leaner, simplify future maintenance, and keep legacy helpers available via the library.

## Detailed Plan

1. **Inventory remaining inline helpers**
   - Catalogue Stage 2 through Stage 5 helper functions that are still defined in the notebook (e.g., `_safe_write_csv`, Stage 3 post-questionnaire parsers, Stage 4 deliverable utilities).
   - Note shared dependencies and decide target `wbdlib` modules for each helper family.
2. **Adopt library-safe CSV writer**
   - Replace the notebook `_safe_write_csv` implementation with `wbdlib.io.safe_write_csv`, updating imports and usage in Stage 2 export cells.
   - Confirm there are no regressions in how result directories are created or filenames are reported.
3. **Extract Stage 3 post-survey helpers**
   - Move the Stage 3 parsing and scoring helpers (`load_post_survey_raw`, `reshape_post_survey_long`, `attach_post_metadata`, `build_recognition_score_frame`, `build_recall_score_frame`, etc.) into a new `wbdlib.post` module with docstrings and type hints.
   - Ensure dependencies such as `canonicalize_title` and survey cleaning utilities are either imported from existing modules or relocated alongside these helpers.
4. **Expose helpers through wbdlib interface**
   - Update `wbdlib/__init__.py` (and any relevant `__all__` lists) so notebooks can import the new post-survey helpers directly.
   - Maintain backward compatibility for any legacy helpers that remain in use.
5. **Refactor notebook cells to use library imports**
   - Update Stage 3 and deliverable cells in `assemble_uv.ipynb` to import the refactored helpers.
   - Remove redundant inline definitions, keeping only minimal orchestration logic in the notebook.
6. **Verify execution path**
   - Re-run the affected notebook cells (Stage 2 exports, Stage 3 assembly, deliverable build) or provide clear instructions for manual execution if automation is not possible in-session.
   - Confirm outputs are written successfully and log any outstanding issues.
7. **Document and prepare follow-up**
   - Summarize structural changes in the task progress log and note remaining helpers (Stage 4/5) that may need further extraction.
   - Identify any tests or validations that should be prioritised in subsequent passes.

## Progress
- 2025-11-17: Plan created and initial helper inventory started; `_safe_write_csv` replacement and Stage 3 extraction queued as next steps.
