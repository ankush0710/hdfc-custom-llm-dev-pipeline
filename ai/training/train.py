"""
ai/training/train.py

Training entry point for the HDFC Qwen3-0.6B LoRA SFT job.

This module bridges the gap between the project's real JSONL datasets
(hdfc_llm_train.jsonl / hdfc_llm_val.jsonl - message-based SFT records)
and the already-validated training stack (ai.training.model.prepare_model,
ai.training.trainer.train_model), which expects a Hugging Face Dataset
with a "text" column. It converts each record's "messages" list into a
single training string using the Qwen3 tokenizer's chat template, then
calls prepare_model()/train_model() exactly as they already exist.

This module does NOT:
- load or use hdfc_llm_test.jsonl (the test set is held out from training)
- modify ai/training/config.py, model.py, lora.py, or trainer.py
- merge LoRA weights into the base model
- implement evaluation (separate, later work)

Usage
-----
    python -m ai.training.train --dry-run
    python -m ai.training.train --max-train-samples 100
    python -m ai.training.train

Run from the project root (C:\\Projects\\hdfc-custom-llm-pipeline) with the
virtual environment activated. Paths are resolved relative to this file's
location, not hardcoded to any absolute user path.
"""

from __future__ import annotations

import argparse
from dataclasses import replace
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from datasets import Dataset
from transformers import AutoTokenizer, PreTrainedTokenizerBase

from ai.training.config import TrainingConfig
from ai.training.model import prepare_model
from ai.training.trainer import TrainingResult, train_model

logger = logging.getLogger(__name__)

# ai/training/train.py -> parents[0]=training, [1]=ai, [2]=repo root
REPO_ROOT = Path(__file__).resolve().parents[2]
TRAIN_JSONL = REPO_ROOT / "hdfc_llm_train.jsonl"
VAL_JSONL = REPO_ROOT / "hdfc_llm_val.jsonl"
# hdfc_llm_test.jsonl is intentionally never referenced anywhere in this
# module - the test set must not be used during training.

VALID_MESSAGE_ROLES = {"system", "user", "assistant"}
DRY_RUN_SAMPLE_SIZE = 5


class DatasetValidationError(RuntimeError):
    """Raised when a JSONL record is malformed or missing a required field.

    Deliberately loud rather than silent: a malformed line always raises,
    identifying the file and line number, instead of being skipped.
    """


# ---------------------------------------------------------------------------
# Loading + validation
# ---------------------------------------------------------------------------


def _validate_record(record: Dict[str, Any], path: Path, line_no: int) -> None:
    """
    Validate that a parsed JSONL record has exactly what this module
    depends on: a record_id (for error messages) and a well-formed
    messages list ending in an assistant turn.

    Deliberately does NOT require instruction/context/response - those
    fields exist in the real dataset but are not consumed here, since the
    "messages" field alone is used to build the training text (per the
    instruction to prefer messages and avoid duplicating content).
    """
    if "record_id" not in record:
        raise DatasetValidationError(
            f"Record missing 'record_id' in {path} at line {line_no}."
        )
    record_id = record["record_id"]

    messages = record.get("messages")
    if not isinstance(messages, list) or not messages:
        raise DatasetValidationError(
            f"Record '{record_id}' in {path} at line {line_no} has a "
            "missing or empty 'messages' list."
        )

    for i, message in enumerate(messages):
        if (
            not isinstance(message, dict)
            or "role" not in message
            or "content" not in message
        ):
            raise DatasetValidationError(
                f"Record '{record_id}' in {path} at line {line_no} has a "
                f"malformed message at index {i} (expected 'role' and "
                "'content' keys)."
            )
        if message["role"] not in VALID_MESSAGE_ROLES:
            raise DatasetValidationError(
                f"Record '{record_id}' in {path} at line {line_no} has an "
                f"unrecognized message role '{message['role']}'."
            )

    if messages[-1]["role"] != "assistant":
        raise DatasetValidationError(
            f"Record '{record_id}' in {path} at line {line_no} does not "
            "end with an assistant message; it cannot be used as an SFT "
            "training target."
        )


def _load_jsonl_records(
    path: Path, limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Load and validate a JSONL file line by line.

    Parameters
    ----------
    path:
        Path to the .jsonl file.
    limit:
        If given, stop reading after collecting this many valid records
        (used for --dry-run's small sample). Lines beyond that point are
        never parsed. If None, the entire file is loaded.

    Raises
    ------
    DatasetValidationError
        On a missing file, malformed JSON, or a record missing required
        fields - always identifying the file and the exact line number.
        Blank/whitespace-only lines are skipped as harmless formatting,
        not treated as malformed content.
    """
    if not path.exists():
        raise DatasetValidationError(f"Dataset file not found: {path}")

    records: List[Dict[str, Any]] = []
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
                raise DatasetValidationError(
                    f"Malformed JSON in {path} at line {line_no}: {exc}"
                ) from exc

            _validate_record(record, path, line_no)
            records.append(record)

    return records


# ---------------------------------------------------------------------------
# messages -> "text" conversion
# ---------------------------------------------------------------------------


def _messages_to_text(
    messages: List[Dict[str, str]], tokenizer: PreTrainedTokenizerBase
) -> str:
    """
    Render a system/user/assistant conversation into one training string
    using the tokenizer's own chat template, rather than hand-assembling
    text from instruction/context/response (which would duplicate content
    already present in `messages`).

    add_generation_prompt=False: the assistant's actual response is
    already the last message, so the full conversation is rendered as-is
    rather than appending an empty prompt for the model to continue.

    enable_thinking=False: see module docstring / response section F for
    why Qwen3's thinking mode is explicitly disabled here.
    """
    return tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=False,
        enable_thinking=False,
    )


def _build_text_dataset(
    records: List[Dict[str, Any]], tokenizer: PreTrainedTokenizerBase
) -> Dataset:
    """Convert validated JSONL records into a HF Dataset with a 'text' column."""
    texts = [_messages_to_text(r["messages"], tokenizer) for r in records]
    return Dataset.from_dict({"text": texts})


# ---------------------------------------------------------------------------
# Tokenizer loading
# ---------------------------------------------------------------------------


def _load_tokenizer(config: TrainingConfig) -> PreTrainedTokenizerBase:
    """Load the tokenizer for config.base_model, ensuring a pad token exists."""
    tokenizer = AutoTokenizer.from_pretrained(config.base_model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    return tokenizer


# ---------------------------------------------------------------------------
# Reporting helpers
# ---------------------------------------------------------------------------


def _print_training_summary(
    config: TrainingConfig,
    train_count: int,
    val_count: int,
    *,
    is_sample: bool = False,
) -> None:
    label = "sample" if is_sample else "examples"
    print("\n=== HDFC Qwen3-0.6B LoRA Training ===")
    print(f"Training {label}:          {train_count}")
    print(f"Validation {label}:        {val_count} (loaded, not used for training yet)")
    print(f"Base model:               {config.base_model}")
    print(f"Output directory:         {config.output_dir}")
    print(f"Max sequence length:      {config.max_seq_length}")
    print(f"Per-device batch size:    {config.per_device_train_batch_size}")
    print(f"Gradient accumulation:    {config.gradient_accumulation_steps}")
    print(f"Num train epochs:         {config.num_train_epochs}")
    print(f"Learning rate:            {config.learning_rate}")
    print(f"LoRA rank (r):            {config.lora_r}")
    print(f"LoRA alpha:               {config.lora_alpha}")
    print("======================================\n")


def _print_dry_run_preview(sample_dataset: Dataset, tokenizer: PreTrainedTokenizerBase) -> None:
    example_text = sample_dataset[0]["text"]
    token_count = len(tokenizer(example_text)["input_ids"])
    preview = example_text[:500] + ("..." if len(example_text) > 500 else "")

    print("--- DRY RUN: sample text preview (no training performed) ---")
    print(f"Sample size built:    {len(sample_dataset)} examples")
    print(f"Example text length:  {len(example_text)} characters, {token_count} tokens")
    print("Example preview:")
    print(preview)
    print("--- END DRY RUN ---\n")


def _print_result_summary(result: TrainingResult) -> None:
    print("\n=== Training Complete ===")
    print(f"Output dir:          {result.output_dir}")
    print(f"Train runtime (s):   {result.train_runtime}")
    print(f"Train loss:          {result.train_loss}")
    print(f"Global step:         {result.global_step}")
    print(f"Peak GPU mem (MB):   {result.peak_gpu_memory_mb}")
    print(f"Trainable params:    {result.trainable_parameters:,}")
    print(f"Total params:        {result.total_parameters:,}")
    print(f"Trainable %:         {result.trainable_percentage}")
    print("==========================\n")


# ---------------------------------------------------------------------------
# CLI + orchestration
# ---------------------------------------------------------------------------


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m ai.training.train",
        description="Train the HDFC Qwen3-0.6B LoRA adapter on hdfc_llm_train.jsonl.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help=(
            "Load/validate a small sample, build the tokenizer and text "
            "representation, and print a preview. Does not start training."
        ),
    )

    parser.add_argument(
        "--max-train-samples",
        type=int,
        default=None,
        help=(
            "Limit ONLY the training dataset to the first N examples "
            "(validation is unaffected). Ignored (capped) under --dry-run, "
            "which always uses a small fixed sample."
        ),
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help=(
            "Override TrainingConfig.output_dir for this run (relative or "
            "absolute path). If omitted, the existing TrainingConfig "
            "default is used unchanged."
        ),
    )

    return parser


def main(argv: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Entry point: parse args, load data, (optionally) train, and return a
    structured result.

    Returns
    -------
    dict
        Under --dry-run: {"dry_run": True, "sample_size": int}.
        Otherwise: TrainingResult.to_dict() from ai.training.trainer.
    """
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )

    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if args.max_train_samples is not None and args.max_train_samples <= 0:
        parser.error("--max-train-samples must be a positive integer.")

    config = TrainingConfig()

    if args.output_dir is not None:
        config = replace(
            config,
            output_dir=Path(args.output_dir),
    )

    config.validate()

    logger.info("Loading tokenizer for '%s'...", config.base_model)
    tokenizer = _load_tokenizer(config)

    if args.dry_run:
        sample_limit = DRY_RUN_SAMPLE_SIZE
        if args.max_train_samples is not None:
            sample_limit = min(sample_limit, args.max_train_samples)

        logger.info("Dry run: loading a %d-record sample from %s", sample_limit, TRAIN_JSONL)
        train_sample = _load_jsonl_records(TRAIN_JSONL, limit=sample_limit)
        val_sample = _load_jsonl_records(VAL_JSONL, limit=sample_limit)

        sample_dataset = _build_text_dataset(train_sample, tokenizer)

        _print_training_summary(
            config, len(train_sample), len(val_sample), is_sample=True
        )
        _print_dry_run_preview(sample_dataset, tokenizer)

        return {"dry_run": True, "sample_size": len(sample_dataset)}

    logger.info("Loading training records from %s", TRAIN_JSONL)
    train_records = _load_jsonl_records(TRAIN_JSONL)
    logger.info("Loading validation records from %s", VAL_JSONL)
    val_records = _load_jsonl_records(VAL_JSONL)
    # hdfc_llm_test.jsonl is never loaded in this module.

    if args.max_train_samples is not None:
        if args.max_train_samples > len(train_records):
            logger.warning(
                "--max-train-samples=%d exceeds available training records "
                "(%d); using all available records.",
                args.max_train_samples,
                len(train_records),
            )
        train_records = train_records[: args.max_train_samples]

    _print_training_summary(config, len(train_records), len(val_records))

    train_dataset = _build_text_dataset(train_records, tokenizer)

    logger.info("Preparing model (base load + LoRA attach)...")
    model = prepare_model(config)

    logger.info("Starting training on %d examples...", len(train_dataset))
    # output_dir is created by train_model() itself; not duplicated here.
    result: TrainingResult = train_model(model, tokenizer, train_dataset, config)

    _print_result_summary(result)
    return result.to_dict()


if __name__ == "__main__":
    main()