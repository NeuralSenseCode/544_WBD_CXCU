# LLM-Based Recall Scoring – Method 2 (Project Context for Copilot)

This document defines the context, data structures, and desired behaviour for an LLM-based qualitative coding pipeline.  
GitHub Copilot (and Copilot Agents) should use this as the reference when generating or modifying code.

---

## 1. Project Goal

We have a CSV of open-ended recall responses to video content.  
Each row = 1 participant’s response to a scene they watched in **long** or **short** format.

We want to:

1. Use an **OpenAI LLM** to score each response on **recall quality**.
2. Store the score as:
   - `recall_score` → **integer 0–100**
   - `confidence_score` → **integer 0–100**
   - `rationale` → short textual explanation of the scoring decision
3. Write a final output file:
   - `coded_responses_full_method2.csv`

The LLM is treated as an **expert qualitative coder**, not as a generative storyteller.

---

## 2. Input Data

### 2.1 Main CSV

File: `sample_open_ended_madmax_long.csv`

Columns (at minimum):

- `id` – unique integer per row (0, 1, 2, …).  
  - If not present, the code **must insert** this as the first column.
- `respondent` – respondent ID
- `group` – experimental group
- `questionnaire` – questionnaire label
- `question_code` – question ID (e.g., `Q13`, `Q18`)
- `question` – question text
- `form` – viewing format (`Long` or `Short`)
- `title` – content title (e.g., `Abbot Elementary`, `Mad Max`, `The Town`)
- `response` – open-ended text response

Assumptions:

- Multiple `question_code` values may exist, but for this method we mainly care about those that ask:
  > “What happened in the scene? Please write a brief summary as accurately as you can…”

### 2.2 Model Answers File

File: `sample_model_answers_events.md`

- Contains **format-specific** scene descriptions for each title (Long / Short).
- For each title + format combo, there is a **chronological list of events**:
  - e.g., “Abbott Elementary – Long Form Scene Events”
  - Each event is numbered (e.g., `1. ...`, `2. ...`, etc.)
- This is the **reference ground truth** for what “accurate recall” looks like.

The code must:

- Parse this `.md` file.
- Build a lookup structure by `(title, format)` → list of model events.

---

## 3. Scoring Targets (What the LLM Should Output)

For each row in the CSV, the LLM must output:

- `recall_score` – **integer from 0 to 100**
  - 0 = no correct recall or completely off-topic.
  - 100 = extremely accurate, detailed recall of most/all key events.
- `confidence_score` – **integer from 0 to 100**
  - 90–100: mapping between response and model events is very clear.
  - 60–80: some ambiguity or vagueness.
  - 30–50: highly vague response or heavy guesswork.
  - 0–20: cannot reasonably interpret the response.
- `rationale` – **short string** (1–3 sentences) explaining:
  - the main reasons for the assigned `recall_score`,
  - e.g., how many key events were recalled and what kind of details were present.

### 3.1 Scoring Guidelines for the LLM (to be embedded into the prompt)

Copilot should help create a system prompt that instructs the LLM roughly as follows:

- You are an expert qualitative coder in applied neuroscience.
- You receive:
  - A list of **MODEL EVENTS** describing the scene (canonical ground truth).
  - A **PARTICIPANT RESPONSE** which is their recall of that scene.
- Task:
  1. Identify which model events are clearly recalled in the response  
     (matching on **meaning**, not exact wording).
  2. Judge how much **detail** is included:
     - Specific character names
     - Places
     - Distinct actions/sequences
     - Any accurate key phrases
  3. Convert your judgement into:
     - `recall_score` (0–100, integer)
     - `confidence_score` (0–100, integer)
     - `rationale` (brief explanation)
- Rough mapping (Copilot should encode this logic in the prompt text, not code):
  - 0–10: completely off-topic, or essentially no overlap with model events.
  - 20–40: only 1–2 events or very vague gist, minimal detail.
  - 40–60: main gist is captured; several correct events but missing many details.
  - 60–80: many key events and some specific details; mostly accurate.
  - 80–100: very accurate, multiple key events plus rich, specific details.
- If the response is blank, “N/A”, “don’t remember”, or clearly irrelevant:
  - `recall_score = 0`
  - `confidence_score` should be **high** (e.g., 90–100),  
    because it’s clear that recall is effectively absent.
- The LLM must **not invent** events that are not present in the model events.
- When uncertain, the LLM should:
  - Lower `confidence_score`
  - Be conservative in `recall_score`.

### 3.2 Required JSON Response Schema

For each row, the LLM must respond with **strict JSON**:

```json
{
  "id": <integer>,
  "recall_score": <integer 0-100>,
  "confidence_score": <integer 0-100>,
  "rationale": "<short explanation>"
}
When batching multiple rows, the LLM should return a JSON list:

json
Copy code
[
  {
    "id": 0,
    "recall_score": 78,
    "confidence_score": 90,
    "rationale": "Captured most of the key events and several specific details about the pizza lie and confession."
  },
  {
    "id": 1,
    "recall_score": 52,
    "confidence_score": 80,
    "rationale": "Recalls the general situation but misses several key beats and character specifics."
  }
]
The code must:

Validate / parse this JSON.

Handle failures (e.g., non-JSON output) by:

Retrying,

Or logging for manual review.

4. Prompt Construction (Per Row / Batch)
For each response, Copilot should help construct a user message like:

text
Copy code
Title: {title}
Format: {format}
Question code: {question_code}
Row ID: {id}

MODEL EVENTS (chronological):
1. {event_1}
2. {event_2}
...
N. {event_N}

PARTICIPANT RESPONSE:
{response_text}

Please evaluate this response:
- Compare it to the MODEL EVENTS.
- Judge how accurately and in how much detail the events are recalled.
- Return a JSON object with:
  - "id" (the Row ID)
  - "recall_score" (0–100, integer)
  - "confidence_score" (0–100, integer)
  - "rationale" (1–3 sentences justifying the score)

Respond with JSON only.
For batch processing, several of these blocks can be concatenated in one request and the model instructed to output a JSON list of results.

5. Pipeline Requirements
Copilot should help create a Python script (or module) that:

Loads inputs:

uv_open_ended_long_recall.csv

model_answers_events.md

Ensures id column:

If missing, add id = range(len(df)).

Parses model events:

From model_answers_events.md

Build a dict: (normalized_title, normalized_format) -> list[events]

E.g., normalise:

"Abbot Elementary" / "Abbott Elementary" → single canonical form.

Formats: "Long" / "Short" → lowercase keys "long", "short".

Batches rows:

Choose a batch size (e.g., 5–20 rows per API call).

For each batch:

Fetch (title, format) → events.

Build the full prompt text for all rows in the batch.

Call the OpenAI Chat Completions API.

Parse the JSON list from the model.

Merges LLM output:

For each JSON object:

Match by id.

Write recall_score, confidence_score, rationale into new columns in the DataFrame.

Outputs final CSV:

File name: coded_responses_full_method2.csv

Contains:

All original columns.

recall_score

confidence_score

rationale

6. OpenAI API Integration Notes
Copilot should assume the following:

API key available via environment variable: OPENAI_API_KEY.

Use the OpenAI chat model (e.g. gpt-4.x or appropriate).

Recommended patterns:

System message: instructions & scoring rules (section 3.1).

User message: batch prompt constructed from data (section 4).

Implement:

Basic rate limiting (sleep between requests).

Error handling:

Retry with exponential backoff on transient errors.

Log which ids failed for possible re-run.

7. Output File Specification
Final target output:

File: coded_responses_full_method2.csv

Structure:

All original columns from uv_open_ended_long_recall.csv (including id).

Plus three new columns:

recall_score (int 0–100)

confidence_score (int 0–100)

rationale (short text)

The code should overwrite coded_responses_full_method2.csv if it already exists.

8. Quality Checks
Copilot should assist in adding basic sanity checks, for example:

Assert:

0 <= recall_score <= 100

0 <= confidence_score <= 100

Count:

How many rows have recall_score as NaN or missing → log them.

Optionally:

Print summary stats:

Mean / SD of recall_score by title, format, question_code.

Save a quick diagnostic report (optional, not required).

9. Implementation Preferences
Language: Python (VS Code).

Likely libraries:

pandas

openai (or the current official OpenAI Python client)

json

re

tqdm (for progress bars, optional).

Structure:

A single main script (e.g. method2_llm_scoring.py) is fine.

Clear functions for:

Loading data

Parsing model events

Building prompts

Calling the LLM

Parsing JSON

Updating the DataFrame

Saving output.

Copilot should use this document as the source of truth for how recall_score, confidence_score, and rationale are defined and how coded_responses_full_method2.csv must be produced.