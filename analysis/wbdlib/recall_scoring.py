"""LLM-powered recall scoring helpers shared across notebooks."""

from __future__ import annotations

import json
import re
import textwrap
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

import pandas as pd


SYSTEM_PROMPT_STAGE51 = textwrap.dedent(
        """
            You are an expert at scoring free-recall responses
            against canonical event lists for media research.
            Compare each PARTICIPANT RESPONSE to the MODEL EVENTS and assign:
            - "recall_score": 0-100
                (0 = no relevant recall, 100 = complete, accurate recall).
        - "confidence_score": 0-100 reflecting certainty in your judgement.
        - "rationale": 1-3 sentences referencing the MODEL EVENTS.
        Return a valid JSON array containing one object per response with keys
        id, recall_score, confidence_score, rationale.
        Do not include any preamble or commentary outside the JSON.
        """
).strip()


def normalise_title(title: str) -> str:
    """Normalise a title for consistent event lookup."""
    cleaned = re.sub(r"\s+", " ", title.strip()).lower()
    cleaned = cleaned.replace(":", "")
    cleaned = cleaned.replace("–", "-")
    cleaned = re.sub(r"\s*-\s*", "-", cleaned)
    return cleaned


def normalise_form(form: str) -> str:
    """Normalise a form string (long/short) for consistent event lookup."""
    form_norm = form.strip().lower()
    form_norm = form_norm.replace("–", "-")
    form_norm = re.sub(r"\s+", " ", form_norm)
    form_norm = form_norm.replace(" form", "").strip()
    alias_map = {
        "lf": "long",
        "longform": "long",
        "long-form": "long",
        "long": "long",
        "sf": "short",
        "shortform": "short",
        "short-form": "short",
        "short": "short",
    }
    if form_norm in alias_map:
        return alias_map[form_norm]
    if "long" in form_norm:
        return "long"
    if "short" in form_norm:
        return "short"
    return form_norm


def parse_model_events(markdown_text: str) -> Dict[Tuple[str, str], List[str]]:
    """Extract event lists from markdown organised by title and form."""
    sections: Dict[Tuple[str, str], List[str]] = {}
    header_pattern = re.compile(
        r"^##\s*(.+?)\s*[-–—]\s*(.+?)\s*$",
        re.MULTILINE,
    )
    matches = list(header_pattern.finditer(markdown_text))
    if not matches:
        raise ValueError("No section headers found in model_answers_events.md")
    for idx, match in enumerate(matches):
        title_raw, form_raw = match.group(1), match.group(2)
        start = match.end()
        has_next = (idx + 1) < len(matches)
        end = matches[idx + 1].start() if has_next else len(markdown_text)
        section_text = markdown_text[start:end]
        pattern = re.compile(r"^\s*\d+\.\s+(.*)$", re.MULTILINE)
        events = [
            evt.strip()
            for evt in pattern.findall(section_text)
            if evt.strip()
        ]
        key = (normalise_title(title_raw), normalise_form(form_raw))
        if key in sections:
            warning_msg = (
                f"Warning: duplicate section for {key}; last occurrence will"
                " be used"
            )
            print(warning_msg)
        sections[key] = events
    return sections


def describe_event_source(
    requested_form: str,
    applied_form: Optional[str],
) -> str:
    """Summarise which event list was applied when building prompts."""
    if not applied_form:
        return "No model events located for this title."
    if requested_form == applied_form:
        return f"{applied_form.title()} form events"
    return (
        f"{applied_form.title()} form events (fallback; requested"
        f" {requested_form})"
    )


def resolve_event_list(
    title: str,
    form: str,
    events_lookup: Dict[Tuple[str, str], List[str]],
    *,
    prefer_short_for_long: bool = False,
) -> Tuple[List[str], str]:
    """Return event list and applied form for a title/form combination."""
    title_key = normalise_title(title or "")
    requested_form = normalise_form(form or "")
    keys_to_try: List[Tuple[str, str]] = []
    if prefer_short_for_long and requested_form == "long":
        keys_to_try.append((title_key, "short"))
    keys_to_try.append((title_key, requested_form))
    for fallback_form in ("short", "long"):
        candidate = (title_key, fallback_form)
        if candidate not in keys_to_try:
            keys_to_try.append(candidate)
    for key in keys_to_try:
        events = events_lookup.get(key)
        if events:
            return events, key[1]
    return [], ""


def _build_prompt_block(row: pd.Series, events: List[str], label: str) -> str:
    """Format a single prompt block for an individual recall response."""
    title_value = row.get("title", "")
    if pd.isna(title_value):
        title_value = ""
    form_value = row.get("form", "")
    if pd.isna(form_value):
        form_value = ""
    question_code = row.get("question_code", "")
    if pd.isna(question_code):
        question_code = ""
    row_id = row.get("id", "")
    if pd.isna(row_id):
        row_id = ""
    response_value = row.get("response", "")
    if pd.isna(response_value):
        response_value = ""
    response_text = str(response_value).strip()
    events_text = (
        "\n".join(f"{idx + 1}. {event}" for idx, event in enumerate(events))
        if events
        else "(No model events available.)"
    )
    return textwrap.dedent(
        f"""
        Title: {title_value}
        Respondent form: {form_value}
        Event list source: {label}
        Question code: {question_code}
        Row ID: {row_id}

        MODEL EVENTS (chronological):
        {events_text}

        PARTICIPANT RESPONSE:
        {response_text}

    Evaluate this response and return a JSON object with keys id, recall_score,
    confidence_score, rationale.
        """
    ).strip()


def build_batch_prompt(
    batch_rows: pd.DataFrame,
    events_lookup: Dict[Tuple[str, str], List[str]],
    *,
    prefer_short_for_long: bool = False,
    include_metadata: bool = False,
) -> Tuple[Any, ...]:
    """Assemble the batched prompt text and optional metadata."""
    blocks: List[str] = []
    missing_keys: List[Tuple[str, str]] = []
    metadata_records: List[Dict[str, Any]] = []
    for _, row in batch_rows.iterrows():
        title_value = row.get("title", "")
        form_value = row.get("form", "")
        events, applied_form = resolve_event_list(
            title_value,
            form_value,
            events_lookup,
            prefer_short_for_long=prefer_short_for_long,
        )
        requested_form = normalise_form(form_value or "")
        title_key = normalise_title(title_value or "")
        if not events:
            missing_keys.append((title_key, requested_form))
        label = describe_event_source(requested_form, applied_form)
        blocks.append(_build_prompt_block(row, events, label))
        if include_metadata:
            row_id_value = row.get("id", pd.NA)
            if pd.isna(row_id_value):
                row_id_clean = None
            else:
                row_id_clean = int(row_id_value)
            metadata_records.append(
                {
                    "id": row_id_clean,
                    "respondent": row.get("respondent"),
                    "title": title_value,
                    "form_requested": form_value,
                    "event_form_used": applied_form or "missing",
                    "event_count": len(events),
                    "event_label": label,
                }
            )
    prompt_text = "\n\n".join(blocks)
    if include_metadata:
        metadata_df = pd.DataFrame(metadata_records)
        return prompt_text, missing_keys, metadata_df
    return prompt_text, missing_keys


def call_llm_batch(
    prompt: str,
    *,
    client_obj: Any,
    model: str,
    system_prompt: str = SYSTEM_PROMPT_STAGE51,
    max_retries: int = 3,
    sleep_seconds: float = 2.0,
) -> str:
    """Invoke an OpenAI Responses client with retry logic."""
    if client_obj is None:
        raise RuntimeError(
            "OpenAI client is not initialised. Set OPENAI_API_KEY before"
            " calling the model."
        )
    payload = [
        {
            "role": "system",
            "content": [{"type": "input_text", "text": system_prompt}],
        },
        {"role": "user", "content": [{"type": "input_text", "text": prompt}]},
    ]
    last_error: Optional[Exception] = None
    for attempt in range(1, max_retries + 1):
        try:
            response = client_obj.responses.create(
                model=model,
                input=payload,
                temperature=0.0,
            )
            return response.output_text
        except Exception as exc:  # pylint: disable=broad-except
            last_error = exc
            wait_for = sleep_seconds * (2 ** (attempt - 1))
            print(
                f"Attempt {attempt} failed: {exc}. Retrying in {wait_for:.1f}s"
            )
            time.sleep(wait_for)
    raise RuntimeError("Failed to retrieve LLM response") from last_error


def parse_llm_json(raw_output: str) -> List[Dict[str, Any]]:
    """Parse LLM JSON response into list of score dictionaries."""
    raw_output = raw_output.strip()
    if raw_output.startswith("```") and raw_output.endswith("```"):
        raw_output = re.sub(r"^```[a-zA-Z]*\n|```$", "", raw_output).strip()
    try:
        parsed = json.loads(raw_output)
    except json.JSONDecodeError:
        objects: List[str] = []
        buffer: List[str] = []
        depth = 0
        in_string = False
        escape = False
        for ch in raw_output:
            if not buffer and ch.isspace():
                continue
            buffer.append(ch)
            if escape:
                escape = False
                continue
            if ch == "\\":
                escape = True
                continue
            if ch == '"':
                in_string = not in_string
                continue
            if not in_string:
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        obj = "".join(buffer).strip()
                        if obj:
                            objects.append(obj)
                        buffer = []
        if buffer:
            candidate = "".join(buffer).strip()
            if candidate:
                objects.append(candidate)
        try:
            parsed = [json.loads(obj) for obj in objects if obj]
        except json.JSONDecodeError as exc:
            preview = raw_output[:200]
            raise ValueError(
                f"Model returned non-JSON payload: {preview}"
            ) from exc
    if isinstance(parsed, dict):
        parsed = [parsed]
    if not isinstance(parsed, list):
        raise ValueError("Expected list of JSON objects from model output")
    cleaned: List[Dict[str, Any]] = []
    for entry in parsed:
        if not isinstance(entry, dict):
            continue
        required = {"id", "recall_score", "confidence_score", "rationale"}
        if not required.issubset(entry):
            continue
        cleaned.append({key: entry[key] for key in required})
    return cleaned


def enrich_dataframe_with_scores(
    df: pd.DataFrame,
    scored_rows: Sequence[Dict[str, Any]],
) -> pd.DataFrame:
    """Merge scored outputs back onto the source dataframe."""
    if not scored_rows:
        return df.copy()
    scored_df = pd.DataFrame(scored_rows).set_index("id")
    merged = df.set_index("id").join(scored_df, how="left")
    return merged.reset_index()


__all__ = [
    "SYSTEM_PROMPT_STAGE51",
    "build_batch_prompt",
    "call_llm_batch",
    "describe_event_source",
    "enrich_dataframe_with_scores",
    "normalise_form",
    "normalise_title",
    "parse_llm_json",
    "parse_model_events",
    "resolve_event_list",
]
