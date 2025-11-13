# Post-Study Survey Responses (Client Deliverable)

This document describes the structure, provenance, and validation notes for the `post_study_survey_responses.csv` file. The table provides a tidy, long-format view of every post-study survey response along with recognition and recall scoring context.

## File summary

- **Location:** `results/post_study_survey_responses.csv`
- **Row count:** 6,059
- **Unique respondents:** 83

## Column definitions

| Column | Description | Type / Values | Notes |
| --- | --- | --- | --- |
| `respondent` | Participant identifier from post survey | string | Trimmed, zero-padded if required |
| `group` | Study group (A–F) | string | Derived from metadata or file name |
| `questionnaire` | Questionnaire label | string | Currently always `Post` |
| `submitted_timestamp` | Submission timestamp (UTC-naïve) | string (`YYYY-MM-DD HH:MM:SS`) | Parsed from Google Form timestamp when available |
| `source_path` | Relative path to raw CSV | string | Example: `data/Post/Group A_ Post Viewing Questionnaire Part Two (Responses) - Form Responses 1.csv` |
| `question_code` | Numeric survey code (e.g., `1.1`, `20`) | string | Blank for administrative rows (timestamp, instructions) |
| `question_text` | Original question header | string | Normalized whitespace only |
| `type` | Question type | string | Values from `post_survey_map` (e.g., `binary`, `likert`, `watch`, open-ended rows blank) |
| `subscale` | Measurement subscale | string | From `post_survey_map` (e.g., `recognition`, `comprehension`) |
| `category` | Recognition category | string | Values `key`, `seen`, `distractor`, `fake`, `unseen`, etc.* |
| `accuracy` | Expected recognition outcome | string | `hit` / `miss` for recognition items **|
| `stimulus_form` | Short vs. long cut label | string | `Short`, `Long`, or blank if unresolved |
| `stimulus_title` | Canonicalized stimulus title | string | Example: `Mad Max`, `Abbot Elementary` |
| `response_raw` | Raw response value | string | Direct string from form |
| `response_clean` | Trimmed response | string | Empty strings promoted to `NaN` |
| `response_numeric` | Numeric interpretation | float | Binary (`0`/`1`) or Likert (1–5) conversions where available |
| `score_value` | Recognition/recall score | float | Recognition (`0/1` or 1–4 confidence) open-ended recall scores |
| `score_confidence` | Confidence or certainty score | float |`confidence_score` from LLM |
| `score_method` | Provenance for `score_value` | string | `stage3_recognition_binary`, `stage3_recognition_confidence`, `stage5_recall_full`, `stage5_recall_keymoment` |
| `score_explanation` | Text rationale | string | Stage 5 recall rationales or recognition interpretation |


*For `category`, the following values can be understood as shown:
`key`: question is about a key moment from target content the respondent was exposed to
`seen`: question is about a moment other than the key moment from target content, which the respondent was exposed to
`unseen`: question is about a moment other than the key moment from target content, which the respondent was not exposed to 
`distractor`: question is about a key moment from filler content the respondent was exposed to
`distractor2`: question is about a moment other than the key moment from filler content, which the respondent was exposed to
`fake`: question is about content that was never shown to the respondent

**For `accuracy`, the following values can be understood as shown:
`hit`: expect a Yes for recogniton
`miss`: expect a No for recogniton

## Scoring

### Recognition
Responses 'Yes' on a `hit` question give a score of 1, responses 'No' on a hit question give 0. Scoring is reversed for `miss`

### Open-ended Recall
 In order to score these questions, a Large Language Model (LLM) was used (gpt-4.1). This model was configured to be a qualitative analyst, and issued the following prompt:

"""
You are an expert at scoring free-recall responses against canonical event lists for media research.
Compare each PARTICIPANT RESPONSE to the MODEL EVENTS and assign:
- "recall_score": 0-100 (0 = no relevant recall, 100 = complete, accurate recall).
- "confidence_score": 0-100 reflecting certainty in your judgement.
- "rationale": 1-3 sentences referencing the MODEL EVENTS.
Return a valid JSON array containing one object per response with keys id, recall_score, confidence_score, rationale.
Do not include any preamble or commentary outside the JSON.
"""

The LLM then scored one response at a time.
