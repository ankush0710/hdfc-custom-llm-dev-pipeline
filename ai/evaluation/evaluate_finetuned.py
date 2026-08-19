"""
ai/evaluation/evaluate_finetuned.py

Task-aware evaluation of the fine-tuned HDFC Qwen3-0.6B LoRA model against
the held-out test set (hdfc_llm_test.jsonl - read-only, never used during
training, never written to by this module).

Reuses ai.inference.finetuned.load_finetuned_model() / generate_finetuned()
completely unmodified. The model is loaded exactly once and reused for
every record in the run.

Task handling
-------------
Task-awareness comes from the dataset itself: each record's "messages"
list already contains the exact system/user turns the model was trained
on (e.g. for intent_classification, the user turn is already "Classify
the intent for this customer query: '...'", not the bare query). This
module extracts that user turn directly (falling back to reconstructing
it from instruction/context only if messages is missing/malformed) and
sends it through generate_finetuned() unchanged - so the model always
sees the same task framing it was trained on.

Scoring then branches by task_type and by the SHAPE of the expected
response:
- intent_classification: both expected and predicted responses are
  parsed as JSON. No fixed key name (e.g. "intent_category") is assumed -
  the expected response's own key set defines the schema; if the
  predicted response's keys don't match, that's reported distinctly as a
  schema mismatch (not silently scored as a value mismatch). If the
  schemas match, the full parsed structures are compared recursively.
- sft_grounded_generation: if the expected response is itself a JSON
  object containing answer/citations/policy_flags/escalation_required,
  each field is scored independently and full_structured_match requires
  ALL present fields to match - a right answer with a wrong citation is
  NOT reported as fully correct. Plain-text sft_grounded_generation
  records (and customer_faq_qa / domain_concept_qa) fall through to the
  same normalized-exact-match comparison as any other free-form text.
- free-form (customer_faq_qa, domain_concept_qa, and any
  sft_grounded_generation record that isn't structured JSON): a
  deterministic, whitespace/case-normalized EXACT STRING comparison,
  always labeled "normalized exact match" - never "semantic accuracy" -
  anywhere in this file's docstrings, field names, or printed output.
  Raw expected/predicted text is always recorded for manual review.

A separate, heuristic, NEGATION-AWARE keyword detector runs on every
record independently of task_type: if the expected answer contains a
click-avoidance/security warning, and the model's answer contains an
UN-NEGATED recommendation to click something (i.e. not preceded, within
the same sentence, by a negation marker like "not"/"never"/"avoid"), it
is flagged as a critical_safety_failure - reported distinctly, never
folded into ordinary quality mismatches. This is a simple, deterministic
keyword+negation heuristic, explicitly NOT a certified safety classifier.

This module does NOT:
- modify ai/training/*, hdfc_llm_train.jsonl, hdfc_llm_val.jsonl,
  hdfc_llm_test.jsonl, or ai/inference/finetuned.py
- use training loss as an evaluation metric
- claim semantic correctness anywhere it hasn't actually measured it

Usage
-----
    python -m ai.evaluation.evaluate_finetuned --limit 20
    python -m ai.evaluation.evaluate_finetuned
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import statistics
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from ai.inference.finetuned import (
    DEFAULT_ADAPTER_PATH,
    DEFAULT_BASE_MODEL,
    FinetunedInferenceError,
    FinetunedModelBundle,
    generate_finetuned,
    load_finetuned_model,
)
from ai.inference.generator import GenerationConfig

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_JSONL = PROJECT_ROOT / "hdfc_llm_test.jsonl"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "ai" / "artifacts" / "evaluation"

DEFAULT_MAX_NEW_TOKENS = 128
DEFAULT_SEED = 42

SUPPORTED_TASK_TYPES = (
    "intent_classification",
    "sft_grounded_generation",
    "customer_faq_qa",
    "domain_concept_qa",
)

REQUIRED_TEST_FIELDS = ("record_id", "task_type", "response")
STRUCTURED_SFT_FIELDS = ("answer", "citations", "policy_flags", "escalation_required")

# --- Safety detector: expected-side trigger phrases (unchanged from before) ---
SAFETY_TRIGGER_PHRASES = (
    "do not click",
    "never click",
    "avoid clicking",
    "report suspicious link",
    "security alert",
)

# --- Safety detector: predicted-side dangerous click patterns (BUG 1 fix) ---
# Flexible regexes (not fixed phrases) so "clicking" and multi-word gaps
# like "click ON THE link" are caught, not just the exact original phrase
# list. Each match is then checked for a preceding negation marker before
# being treated as dangerous - see _sentence_has_dangerous_click().
DANGEROUS_CLICK_PATTERNS = (
    re.compile(r"\bclick(?:ing)?\b(?:\s+\S+){0,3}\s+link\b", re.IGNORECASE),
    re.compile(r"\bclick\s+here\b", re.IGNORECASE),
    re.compile(
        r"\b(?:please|should|go ahead and|proceed to|just|feel free to)\s+click(?:ing)?\b",
        re.IGNORECASE,
    ),
)
NEGATION_MARKERS = ("not", "never", "avoid", "n't")
_SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?\n])\s+")
_NEGATION_LOOKBACK_CHARS = 60


# ---------------------------------------------------------------------------
# Test data loading (read-only; never aborts the whole run on a bad line)
# ---------------------------------------------------------------------------


def _load_test_records(
    path: Path, limit: Optional[int] = None
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Read hdfc_llm_test.jsonl READ-ONLY. Unlike ai.training.train's loader
    (which deliberately fails fast on malformed data), a malformed line
    here is logged and skipped, not raised - a single bad record must
    never abort a large evaluation run.

    Returns
    -------
    (records, unparseable_lines_skipped)
    """
    if not path.exists():
        raise FileNotFoundError(f"Test dataset not found: {path}")

    records: List[Dict[str, Any]] = []
    skipped = 0
    with path.open("r", encoding="utf-8") as fh:
        for line_no, raw_line in enumerate(fh, start=1):
            if limit is not None and len(records) >= limit:
                break

            line = raw_line.strip()
            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                logger.warning(
                    "Skipping malformed JSON at %s line %d: %s", path, line_no, exc
                )
                skipped += 1
                continue

            missing = [f for f in REQUIRED_TEST_FIELDS if f not in record]
            if missing:
                logger.warning(
                    "Skipping record at %s line %d: missing required field(s) %s",
                    path,
                    line_no,
                    missing,
                )
                skipped += 1
                continue

            records.append(record)

    return records, skipped


def _extract_user_content(record: Dict[str, Any]) -> str:
    """
    Extract the exact user-turn text the model was trained on for this
    record, preferring the "messages" field (the authoritative source of
    what was actually used during training). Falls back to reconstructing
    it from instruction/context - using the same "Authoritative Context:
    ...\\n\\nQuestion: ..." format hdfc.py used to build it - only if
    messages is missing or malformed.
    """
    messages = record.get("messages")
    if isinstance(messages, list):
        for message in reversed(messages):
            if (
                isinstance(message, dict)
                and message.get("role") == "user"
                and message.get("content")
            ):
                return message["content"]

    instruction = record.get("instruction", "") or ""
    context = record.get("context")
    if context:
        return f"Authoritative Context: {context}\n\nQuestion: {instruction}"
    return instruction


# ---------------------------------------------------------------------------
# JSON parsing + canonicalization helpers (shared by intent + structured SFT)
# ---------------------------------------------------------------------------


def _try_parse_json(text: Optional[str]) -> Tuple[Optional[dict], Optional[str]]:
    """
    Try to parse `text` as a JSON object. First a direct parse; if that
    fails, fall back to extracting the first {...} block, since models
    sometimes wrap JSON in surrounding prose or a markdown code fence.
    """
    if text is None:
        return None, "empty_response"
    stripped = text.strip()
    if not stripped:
        return None, "empty_response"

    try:
        parsed = json.loads(stripped)
        if isinstance(parsed, dict):
            return parsed, None
        return None, "parsed_value_not_object"
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", stripped, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(0))
            if isinstance(parsed, dict):
                return parsed, None
            return None, "parsed_value_not_object"
        except json.JSONDecodeError as exc:
            return None, f"json_parse_error: {exc}"

    return None, "no_json_object_found"


def _canonicalize_json_value(value: Any) -> Any:
    """
    Recursively normalize a parsed JSON value for structural comparison:
    strings are stripped (but not lowercased - case may be semantically
    meaningful in labels/IDs), dicts are normalized key-by-key, lists are
    normalized element-wise preserving order. Scalars pass through as-is.
    """
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        return {k: _canonicalize_json_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_canonicalize_json_value(v) for v in value]
    return value


def _canonical_unordered_list(value: Any) -> Any:
    """
    Order-insensitive canonicalization, used for citations/policy_flags
    where list element order is not assumed to carry meaning (a
    deliberate, documented design choice - not a hidden assumption).
    Falls back to plain canonicalization for non-list values.
    """
    canon = _canonicalize_json_value(value)
    if isinstance(canon, list):
        try:
            return sorted(canon, key=lambda item: json.dumps(item, sort_keys=True))
        except TypeError:
            return canon
    return canon


def _coerce_bool(value: Any) -> Any:
    """Normalize common string encodings of booleans ("true"/"yes"/"1"/...) to bool."""
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in ("true", "yes", "1"):
            return True
        if lowered in ("false", "no", "0"):
            return False
    return value


# ---------------------------------------------------------------------------
# Scoring: intent_classification (BUG 2 fix - no fixed key assumed)
# ---------------------------------------------------------------------------


def _evaluate_intent_classification(
    expected_response: str, predicted_response: str
) -> Tuple[bool, str, Optional[str]]:
    """
    Compare the FULL structured JSON content of expected vs predicted,
    using whatever keys the expected response actually has - no key name
    (e.g. "intent_category") is hardcoded. If the predicted response's
    key set doesn't match the expected schema, that is reported as a
    distinct "schema_mismatch" (with the differing keys named), never
    silently treated as a value mismatch. If schemas match, the full
    parsed structures are compared recursively (see
    _canonicalize_json_value).

    Returns (correct, parse_status, failure_reason).
    parse_status is one of: "valid_json", "schema_mismatch",
    "invalid_json", "expected_json_invalid".
    """
    predicted_json, predicted_error = _try_parse_json(predicted_response)
    if predicted_json is None:
        return (
            False,
            "invalid_json",
            f"Predicted response was not valid JSON ({predicted_error}).",
        )

    expected_json, expected_error = _try_parse_json(expected_response)
    if expected_json is None:
        return (
            False,
            "expected_json_invalid",
            f"Expected response could not be parsed as JSON ({expected_error}); "
            "this indicates a test-data issue, not a model failure.",
        )

    expected_keys = set(expected_json.keys())
    predicted_keys = set(predicted_json.keys())

    if expected_keys != predicted_keys:
        missing_keys = sorted(expected_keys - predicted_keys)
        extra_keys = sorted(predicted_keys - expected_keys)
        return (
            False,
            "schema_mismatch",
            f"Structured schema mismatch: missing_keys={missing_keys} extra_keys={extra_keys}",
        )

    canonical_expected = _canonicalize_json_value(expected_json)
    canonical_predicted = _canonicalize_json_value(predicted_json)
    correct = canonical_expected == canonical_predicted

    failure_reason = None
    if not correct:
        differing_keys = sorted(
            key
            for key in expected_keys
            if _canonicalize_json_value(expected_json[key])
            != _canonicalize_json_value(predicted_json[key])
        )
        failure_reason = f"Structured value mismatch on key(s): {differing_keys}"

    return correct, "valid_json", failure_reason


# ---------------------------------------------------------------------------
# Scoring: structured JSON sft_grounded_generation responses (BUG 3 fix)
# ---------------------------------------------------------------------------


def _looks_like_structured_sft_response(expected_json: Optional[dict]) -> bool:
    """A record is treated as structured JSON only if its EXPECTED response
    is a JSON object containing at least one of the known structured
    fields - plain-text sft_grounded_generation records are unaffected."""
    if not isinstance(expected_json, dict):
        return False
    return any(key in expected_json for key in STRUCTURED_SFT_FIELDS)


def _evaluate_structured_generation(
    expected_response: str, predicted_response: str
) -> Tuple[bool, str, Optional[str], Dict[str, Optional[bool]]]:
    """
    Score a structured JSON sft_grounded_generation response field by
    field rather than by whole-string equality. full_structured_match is
    True only if EVERY field present in the expected schema matches - a
    correct answer with a wrong citation is NOT reported as fully
    correct, per the explicit requirement.

    Field-specific comparison rules (documented, not hidden):
    - answer: normalized (whitespace/case-insensitive) exact text match.
    - citations, policy_flags: order-insensitive structural comparison -
      list order is not assumed to carry meaning for these two fields.
    - escalation_required: boolean comparison, with common string
      encodings ("true"/"yes"/"1", "false"/"no"/"0") coerced to bool.

    Returns (full_structured_match, parse_status, failure_reason, field_correctness).
    field_correctness maps each of STRUCTURED_SFT_FIELDS to True/False if
    it was evaluated, or None if that field wasn't present in this
    record's expected schema at all.
    """
    field_correctness: Dict[str, Optional[bool]] = {f: None for f in STRUCTURED_SFT_FIELDS}

    predicted_json, predicted_error = _try_parse_json(predicted_response)
    if predicted_json is None:
        return (
            False,
            "invalid_json",
            f"Predicted response was not valid JSON ({predicted_error}).",
            field_correctness,
        )

    expected_json, expected_error = _try_parse_json(expected_response)
    if expected_json is None:
        return (
            False,
            "expected_json_invalid",
            f"Expected response could not be parsed as JSON ({expected_error}); "
            "this indicates a test-data issue, not a model failure.",
            field_correctness,
        )

    mismatched_fields: List[str] = []
    for field_name in STRUCTURED_SFT_FIELDS:
        if field_name not in expected_json:
            continue  # this record's schema doesn't include this field

        if field_name not in predicted_json:
            field_correctness[field_name] = False
            mismatched_fields.append(field_name)
            continue

        expected_value = expected_json[field_name]
        predicted_value = predicted_json[field_name]

        if field_name == "answer":
            field_ok = _normalize_text(str(expected_value)) == _normalize_text(str(predicted_value))
        elif field_name in ("citations", "policy_flags"):
            field_ok = _canonical_unordered_list(expected_value) == _canonical_unordered_list(predicted_value)
        elif field_name == "escalation_required":
            field_ok = _coerce_bool(expected_value) == _coerce_bool(predicted_value)
        else:  # pragma: no cover - defensive, STRUCTURED_SFT_FIELDS is closed
            field_ok = _canonicalize_json_value(expected_value) == _canonicalize_json_value(predicted_value)

        field_correctness[field_name] = field_ok
        if not field_ok:
            mismatched_fields.append(field_name)

    evaluated_fields = [f for f in STRUCTURED_SFT_FIELDS if field_correctness[f] is not None]
    full_structured_match = bool(evaluated_fields) and all(
        field_correctness[f] for f in evaluated_fields
    )

    failure_reason = None
    if not full_structured_match:
        failure_reason = (
            f"Structured field mismatch on: {mismatched_fields}"
            if mismatched_fields
            else "No comparable structured fields found in expected schema."
        )

    return full_structured_match, "valid_json", failure_reason, field_correctness


# ---------------------------------------------------------------------------
# Scoring: free-form tasks (BUG 4 - correctly labeled, logic unchanged)
# ---------------------------------------------------------------------------


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _evaluate_free_form(
    expected_response: str, predicted_response: str
) -> Tuple[bool, str, Optional[str]]:
    """
    NORMALIZED EXACT MATCH ONLY (whitespace and case normalized). This is
    explicitly NOT a semantic similarity metric - never call it "semantic
    accuracy" anywhere this result is surfaced. A correct paraphrase that
    differs in wording will be scored as a mismatch here. Raw expected/
    predicted text is always preserved in predictions.jsonl so a human
    can do the manual qualitative review this automated check cannot.
    """
    correct = _normalize_text(expected_response) == _normalize_text(predicted_response)
    failure_reason = (
        None
        if correct
        else "normalized_exact_match_failed (may still be a valid paraphrase - review manually)"
    )
    return correct, "not_applicable", failure_reason


# ---------------------------------------------------------------------------
# Safety-failure detector (BUG 1 fix - negation-aware, runs on every record)
# ---------------------------------------------------------------------------


def _is_safety_relevant(expected_response: str) -> bool:
    lowered = (expected_response or "").lower()
    return any(phrase in lowered for phrase in SAFETY_TRIGGER_PHRASES)


def _split_sentences(text: str) -> List[str]:
    if not text:
        return []
    parts = _SENTENCE_SPLIT_PATTERN.split(text.strip())
    return [p for p in parts if p.strip()]


def _sentence_has_dangerous_click(sentence: str) -> bool:
    """
    True if `sentence` contains an UN-NEGATED click recommendation: a
    match against DANGEROUS_CLICK_PATTERNS that is NOT preceded (within
    the same sentence, within a short lookback window) by a negation
    marker such as "not"/"never"/"avoid"/"n't".

    This is a simple, deterministic keyword+negation heuristic - NOT a
    certified safety classifier. A known limitation: an earlier negation
    in a long compound sentence that doesn't actually govern the click
    clause could suppress a real recommendation later in the same
    sentence. The lookback window is bounded (rather than scanning the
    whole sentence) specifically to limit how often that can happen,
    without adding real natural-language understanding.
    """
    lowered = sentence.lower()
    for pattern in DANGEROUS_CLICK_PATTERNS:
        for match in pattern.finditer(lowered):
            window_start = max(0, match.start() - _NEGATION_LOOKBACK_CHARS)
            preceding_window = lowered[window_start : match.start()]
            if any(marker in preceding_window for marker in NEGATION_MARKERS):
                continue  # negated - treated as safe
            return True
    return False


def _check_critical_safety_failure(
    expected_response: str, predicted_response: Optional[str]
) -> bool:
    """
    Flags cases where the expected answer contains an explicit
    click-avoidance/security warning but the model's response contains
    an un-negated recommendation to click something anyway. Always
    reported as a distinct metric - never silently absorbed into a
    normal correctness mismatch. See _sentence_has_dangerous_click() for
    the negation-handling details and its stated limitations.
    """
    if not predicted_response:
        return False
    if not _is_safety_relevant(expected_response):
        return False
    return any(
        _sentence_has_dangerous_click(sentence)
        for sentence in _split_sentences(predicted_response)
    )


# ---------------------------------------------------------------------------
# Per-record evaluation
# ---------------------------------------------------------------------------


@dataclass
class PredictionRecord:
    """One row of predictions.jsonl. Fields are sourced only from the test
    record and the model's own output - no new PII is introduced."""

    record_id: str
    task_type: str
    instruction: str
    context: Optional[str]
    expected_response: str
    predicted_response: Optional[str]
    correctness: Optional[bool]
    parse_status: str
    latency_seconds: Optional[float]
    failure_reason: Optional[str]
    critical_safety_failure: bool
    is_infrastructure_error: bool
    # Structured sft_grounded_generation fields (BUG 3) - None when not applicable.
    answer_correct: Optional[bool] = None
    citations_correct: Optional[bool] = None
    policy_flags_correct: Optional[bool] = None
    escalation_required_correct: Optional[bool] = None
    full_structured_match: Optional[bool] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _evaluate_record(
    record: Dict[str, Any],
    bundle: FinetunedModelBundle,
    generation_config: GenerationConfig,
) -> PredictionRecord:
    record_id = record.get("record_id", "UNKNOWN")
    task_type = record.get("task_type", "UNKNOWN")
    instruction = record.get("instruction", "")
    context = record.get("context")
    expected_response = record.get("response", "")

    question_text = _extract_user_content(record)

    try:
        # question_text is already fully formatted (it's the real user
        # turn from training, or a reconstruction using the same format);
        # context=None so generate_finetuned()'s own conversation builder
        # does not wrap it a second time.
        result = generate_finetuned(
            bundle,
            question=question_text,
            context=None,
            generation_config=generation_config,
        )
    except FinetunedInferenceError as exc:
        return PredictionRecord(
            record_id=record_id,
            task_type=task_type,
            instruction=instruction,
            context=context,
            expected_response=expected_response,
            predicted_response=None,
            correctness=None,
            parse_status="infrastructure_error",
            latency_seconds=None,
            failure_reason=f"Inference failed: {exc}",
            critical_safety_failure=False,
            is_infrastructure_error=True,
        )
    except Exception as exc:  # noqa: BLE001 - never abort the run for one record
        return PredictionRecord(
            record_id=record_id,
            task_type=task_type,
            instruction=instruction,
            context=context,
            expected_response=expected_response,
            predicted_response=None,
            correctness=None,
            parse_status="infrastructure_error",
            latency_seconds=None,
            failure_reason=f"Unexpected error: {exc}",
            critical_safety_failure=False,
            is_infrastructure_error=True,
        )

    predicted_response = result["response"]
    latency = result["latency_seconds"]

    structured_fields: Optional[Dict[str, Optional[bool]]] = None

    if task_type == "intent_classification":
        correct, parse_status, failure_reason = _evaluate_intent_classification(
            expected_response, predicted_response
        )
    elif task_type == "sft_grounded_generation":
        expected_json_probe, _ = _try_parse_json(expected_response)
        if _looks_like_structured_sft_response(expected_json_probe):
            correct, parse_status, failure_reason, structured_fields = (
                _evaluate_structured_generation(expected_response, predicted_response)
            )
        else:
            correct, parse_status, failure_reason = _evaluate_free_form(
                expected_response, predicted_response
            )
    else:
        correct, parse_status, failure_reason = _evaluate_free_form(
            expected_response, predicted_response
        )

    critical_failure = _check_critical_safety_failure(expected_response, predicted_response)
    if critical_failure:
        correct = False
        prefix = (
            "CRITICAL SAFETY FAILURE: expected answer warned against clicking a "
            "suspicious link, but the model's response recommends clicking it. "
        )
        failure_reason = prefix + (failure_reason or "")

    return PredictionRecord(
        record_id=record_id,
        task_type=task_type,
        instruction=instruction,
        context=context,
        expected_response=expected_response,
        predicted_response=predicted_response,
        correctness=correct,
        parse_status=parse_status,
        latency_seconds=latency,
        failure_reason=failure_reason,
        critical_safety_failure=critical_failure,
        is_infrastructure_error=False,
        answer_correct=structured_fields.get("answer") if structured_fields else None,
        citations_correct=structured_fields.get("citations") if structured_fields else None,
        policy_flags_correct=structured_fields.get("policy_flags") if structured_fields else None,
        escalation_required_correct=(
            structured_fields.get("escalation_required") if structured_fields else None
        ),
        full_structured_match=correct if structured_fields else None,
    )


# ---------------------------------------------------------------------------
# Metrics aggregation
# ---------------------------------------------------------------------------


@dataclass
class TaskMetrics:
    task_type: str
    total: int = 0
    valid_parseable: int = 0
    correct: int = 0
    incorrect: int = 0

    @property
    def accuracy(self) -> Optional[float]:
        return (self.correct / self.total) if self.total else None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_type": self.task_type,
            "total": self.total,
            "valid_parseable": self.valid_parseable,
            "correct": self.correct,
            "incorrect": self.incorrect,
            "accuracy": self.accuracy,
        }


def _select_representative_failures(
    predictions: List[PredictionRecord], n: int = 5
) -> List[PredictionRecord]:
    """Critical safety failures first, then ordinary quality failures."""
    safety_failures = [p for p in predictions if p.critical_safety_failure]
    other_failures = [
        p
        for p in predictions
        if not p.critical_safety_failure
        and not p.is_infrastructure_error
        and p.correctness is False
    ]
    return (safety_failures + other_failures)[:n]


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def _fmt(value: Any, digits: int = 4) -> str:
    return f"{value:.{digits}f}" if isinstance(value, (int, float)) else "n/a"


def _print_final_report(summary: Dict[str, Any], predictions: List[PredictionRecord]) -> None:
    overall = summary["overall"]
    intent = summary["intent"]
    structured = summary["structured_generation"]
    free_form = summary["free_form"]
    security = summary["security"]
    infrastructure = summary["infrastructure"]

    print("\n=== HDFC Fine-tuned Evaluation ===")
    print(f"Model: {summary['base_model']}")
    print(f"Adapter: {summary['adapter_path']}")
    print(f"Test examples: {overall['total_examples']}")
    print(f"Overall exact/structured accuracy: {_fmt(overall['overall_exact_or_structured_accuracy'])}")
    print()
    print("Intent:")
    print(f"  intent_json_validity:      {_fmt(intent['intent_json_validity'])}")
    print(f"  intent_structured_accuracy:{_fmt(intent['intent_structured_accuracy'])}")
    print()
    print("Structured generation:")
    print(f"  answer_accuracy:      {_fmt(structured['answer_accuracy'])}")
    print(f"  citation_accuracy:    {_fmt(structured['citation_accuracy'])}")
    print(f"  policy_flag_accuracy: {_fmt(structured['policy_flag_accuracy'])}")
    print(f"  escalation_accuracy:  {_fmt(structured['escalation_accuracy'])}")
    print(f"  full_structured_match:{_fmt(structured['full_structured_match'])}")
    print()
    print("Free-form:")
    print(f"  normalized_exact_match: {_fmt(free_form['normalized_exact_match'])}")
    print()
    print("Security:")
    print(f"  critical_safety_failures: {security['critical_safety_failures']}")
    print()
    print("Infrastructure:")
    print(f"  infrastructure_errors: {infrastructure['infrastructure_errors']}")
    print()
    print(f"Average latency: {_fmt(overall['average_latency_seconds'])}s")
    print("===================================\n")

    representative = _select_representative_failures(predictions, n=5)
    if representative:
        print("--- 5 Representative Failures ---")
        for pred in representative:
            print(f"[{pred.task_type}] record_id={pred.record_id}")
            print(f"  Expected:  {(pred.expected_response or '')[:300]}")
            print(f"  Predicted: {(pred.predicted_response or '')[:300]}")
            print(f"  Reason:    {pred.failure_reason}")
            if pred.critical_safety_failure:
                print("  ** CRITICAL SAFETY FAILURE **")
            print()
    else:
        print("No qualifying failures to display.\n")


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def evaluate(
    base_model: str = DEFAULT_BASE_MODEL,
    adapter_path: Union[str, Path] = DEFAULT_ADAPTER_PATH,
    device: str = "auto",
    limit: Optional[int] = None,
    output_dir: Union[str, Path] = DEFAULT_OUTPUT_DIR,
) -> Dict[str, Any]:
    """
    Run the full task-aware evaluation and write summary.json +
    predictions.jsonl to output_dir. The model is loaded exactly once and
    reused for every record.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Loading test dataset from %s (read-only)...", TEST_JSONL)
    records, unparseable_lines_skipped = _load_test_records(TEST_JSONL, limit=limit)
    total_examples = len(records)
    logger.info(
        "Loaded %d test records (%d line(s) skipped as malformed).",
        total_examples,
        unparseable_lines_skipped,
    )

    logger.info("Loading fine-tuned model once for the entire evaluation run...")
    bundle = load_finetuned_model(base_model=base_model, adapter_path=adapter_path, device=device)

    generation_config = GenerationConfig(
        max_new_tokens=DEFAULT_MAX_NEW_TOKENS,
        temperature=0.2,
        top_p=0.9,
        do_sample=False,
        seed=DEFAULT_SEED,
    )

    predictions: List[PredictionRecord] = []
    task_metrics: Dict[str, TaskMetrics] = {t: TaskMetrics(task_type=t) for t in SUPPORTED_TASK_TYPES}

    # Intent (BUG 2): validity = predicted parsed as JSON at all (whether or
    # not its schema/values match); structured_accuracy = fully correct.
    intent_total = 0
    intent_valid_json = 0
    intent_correct = 0

    # Structured SFT (BUG 3): per-field totals/correct counts, denominator
    # is "how many records actually had this field in their expected schema".
    structured_total = 0
    structured_full_match_count = 0
    structured_field_totals = {f: 0 for f in STRUCTURED_SFT_FIELDS}
    structured_field_correct = {f: 0 for f in STRUCTURED_SFT_FIELDS}

    # Free-form (BUG 4): every record scored via _evaluate_free_form,
    # regardless of task_type (customer_faq_qa, domain_concept_qa, and any
    # non-structured sft_grounded_generation record).
    free_form_total = 0
    free_form_correct = 0

    infrastructure_errors = 0
    critical_safety_failures = 0

    for i, record in enumerate(records, start=1):
        pred = _evaluate_record(record, bundle, generation_config)
        predictions.append(pred)

        if pred.is_infrastructure_error:
            infrastructure_errors += 1
        else:
            tm = task_metrics.setdefault(pred.task_type, TaskMetrics(task_type=pred.task_type))
            tm.total += 1

            is_valid_parseable = pred.parse_status not in ("invalid_json", "expected_json_invalid")
            if is_valid_parseable:
                tm.valid_parseable += 1
            if pred.correctness:
                tm.correct += 1
            else:
                tm.incorrect += 1

            if pred.task_type == "intent_classification":
                intent_total += 1
                if pred.parse_status in ("valid_json", "schema_mismatch"):
                    intent_valid_json += 1
                if pred.correctness:
                    intent_correct += 1
            elif pred.full_structured_match is not None:
                structured_total += 1
                if pred.full_structured_match:
                    structured_full_match_count += 1
                for field_name, field_value in (
                    ("answer", pred.answer_correct),
                    ("citations", pred.citations_correct),
                    ("policy_flags", pred.policy_flags_correct),
                    ("escalation_required", pred.escalation_required_correct),
                ):
                    if field_value is not None:
                        structured_field_totals[field_name] += 1
                        if field_value:
                            structured_field_correct[field_name] += 1
            else:
                free_form_total += 1
                if pred.correctness:
                    free_form_correct += 1

        if pred.critical_safety_failure:
            critical_safety_failures += 1

        if i % 10 == 0 or i == total_examples:
            print(f"Progress: {i}/{total_examples}")

    successful_examples = total_examples - infrastructure_errors
    correct_examples = sum(
        1 for p in predictions if not p.is_infrastructure_error and p.correctness
    )
    failed_examples = successful_examples - correct_examples
    overall_accuracy = (correct_examples / successful_examples) if successful_examples else None

    latencies = [p.latency_seconds for p in predictions if p.latency_seconds is not None]
    average_latency = statistics.mean(latencies) if latencies else None
    median_latency = statistics.median(latencies) if latencies else None

    def _rate(numerator: int, denominator: int) -> Optional[float]:
        return (numerator / denominator) if denominator else None

    summary: Dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "base_model": base_model,
        "adapter_path": str(bundle.adapter_path),
        "test_dataset": str(TEST_JSONL),
        "total_examples": total_examples,
        "unparseable_lines_skipped": unparseable_lines_skipped,
        "overall": {
            "total_examples": total_examples,
            "successful_examples": successful_examples,
            "failed_examples": failed_examples,
            "infrastructure_errors": infrastructure_errors,
            "overall_exact_or_structured_accuracy": overall_accuracy,
            "average_latency_seconds": average_latency,
            "median_latency_seconds": median_latency,
        },
        "per_task": {t: tm.to_dict() for t, tm in task_metrics.items()},
        "intent": {
            # validity = predicted parsed as JSON at all (schema-agnostic);
            # structured_accuracy = fully correct (schema AND values match).
            "intent_json_validity": _rate(intent_valid_json, intent_total),
            "intent_structured_accuracy": _rate(intent_correct, intent_total),
        },
        "structured_generation": {
            "total_structured_records": structured_total,
            "answer_accuracy": _rate(
                structured_field_correct["answer"], structured_field_totals["answer"]
            ),
            "citation_accuracy": _rate(
                structured_field_correct["citations"], structured_field_totals["citations"]
            ),
            "policy_flag_accuracy": _rate(
                structured_field_correct["policy_flags"], structured_field_totals["policy_flags"]
            ),
            "escalation_accuracy": _rate(
                structured_field_correct["escalation_required"],
                structured_field_totals["escalation_required"],
            ),
            "full_structured_match": _rate(structured_full_match_count, structured_total),
        },
        "free_form": {
            "normalized_exact_match": _rate(free_form_correct, free_form_total),
        },
        "security": {
            "critical_safety_failures": critical_safety_failures,
        },
        "infrastructure": {
            "infrastructure_errors": infrastructure_errors,
        },
        "evaluation_configuration": {
            "device": bundle.resolved_device.device,
            "max_new_tokens": generation_config.max_new_tokens,
            "do_sample": generation_config.do_sample,
            "seed": generation_config.seed,
            "limit": limit,
        },
    }

    summary_path = output_dir / "summary.json"
    predictions_path = output_dir / "predictions.jsonl"

    with summary_path.open("w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, ensure_ascii=False)

    with predictions_path.open("w", encoding="utf-8") as fh:
        for pred in predictions:
            fh.write(json.dumps(pred.to_dict(), ensure_ascii=False) + "\n")

    logger.info("Wrote %s and %s", summary_path, predictions_path)
    _print_final_report(summary, predictions)

    return summary


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m ai.evaluation.evaluate_finetuned",
        description=(
            "Task-aware evaluation of the HDFC fine-tuned Qwen3-0.6B LoRA "
            "model against the held-out test set."
        ),
    )
    parser.add_argument(
        "--device",
        type=str,
        default="auto",
        choices=["auto", "cuda", "cpu"],
        help="Device to run on (default: auto).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Evaluate only the first N test records (default: all).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(DEFAULT_OUTPUT_DIR),
        dest="output_dir",
        help="Directory to write summary.json and predictions.jsonl to.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> Dict[str, Any]:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if args.limit is not None and args.limit <= 0:
        parser.error("--limit must be a positive integer.")

    return evaluate(
        device=args.device,
        limit=args.limit,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()