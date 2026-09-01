import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from datasets import Dataset
from transformers import AutoTokenizer, PreTrainedTokenizerBase

from ai.training.config import TrainingConfig
from ai.training.model import prepare_model
from ai.training.trainer import train_model, TrainingProgressCallback

logger = logging.getLogger(__name__)


class AITrainingAdapter:

    @staticmethod
    def _load_raw_records(dataset_path: Path) -> List[Dict[str, Any]]:
        """Load records from jsonl, json, csv, or excel files into structured dicts."""
        if not dataset_path.exists():
            raise FileNotFoundError(f"Dataset file not found: {dataset_path}")

        suffix = dataset_path.suffix.lower()
        records: List[Dict[str, Any]] = []

        if suffix == ".jsonl":
            with dataset_path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        records.append(json.loads(line))

        elif suffix == ".json":
            with dataset_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    records = data
                elif isinstance(data, dict):
                    records = [data]

        elif suffix in {".csv", ".xlsx"}:
            df = pd.read_csv(dataset_path) if suffix == ".csv" else pd.read_excel(dataset_path)
            records = df.to_dict(orient="records")

        else:
            raise ValueError(f"Unsupported dataset format: {suffix}")

        return records

    @staticmethod
    def _record_to_messages(record: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract or construct a standard conversation message list from a record."""
        # 1. Direct 'messages' list
        if "messages" in record and isinstance(record["messages"], list):
            return record["messages"]

        # 2. 'question' / 'context' / 'response' or 'answer'
        question = record.get("question") or record.get("instruction") or record.get("prompt") or ""
        context = record.get("context") or ""
        response = record.get("response") or record.get("answer") or record.get("output") or record.get("completion") or ""

        user_content = f"Context:\n{context.strip()}\n\nQuestion:\n{question.strip()}" if context.strip() else question.strip()

        return [
            {"role": "system", "content": "You are a helpful and accurate HDFC Bank assistant."},
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": str(response).strip()},
        ]

    @classmethod
    def prepare_dataset(
        cls,
        dataset_path: Path,
        tokenizer: PreTrainedTokenizerBase,
    ) -> Dataset:
        """Convert any supported dataset format into a Hugging Face Dataset with a 'text' column."""
        records = cls._load_raw_records(dataset_path)
        if not records:
            raise ValueError(f"Dataset at {dataset_path} contains no valid records.")

        texts: List[str] = []
        for r in records:
            messages = cls._record_to_messages(r)
            formatted_text = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=False,
                enable_thinking=False,
            )
            texts.append(formatted_text)

        return Dataset.from_dict({"text": texts})

    @classmethod
    def train(
        cls,
        base_model: str,
        dataset_path: str,
        output_dir: str,
        epochs: float = 1.0,
        learning_rate: float = 2e-4,
        batch_size: int = 1,
        max_seq_length: int = 256,
        progress_callback: Optional[Any] = None,
        should_stop_callback: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Execute full training pipeline for a given base model and dataset."""
        data_p = Path(dataset_path)
        out_p = Path(output_dir)
        out_p.mkdir(parents=True, exist_ok=True)

        config = TrainingConfig(
            base_model=base_model,
            dataset_path=data_p,
            output_dir=out_p,
            num_train_epochs=epochs,
            learning_rate=learning_rate,
            per_device_train_batch_size=batch_size,
            max_seq_length=max_seq_length,
        )
        config.validate()

        logger.info("Loading tokenizer for '%s'...", config.base_model)
        tokenizer = AutoTokenizer.from_pretrained(config.base_model)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        logger.info("Preparing dataset from '%s'...", data_p)
        train_dataset = cls.prepare_dataset(data_p, tokenizer)

        logger.info("Preparing model with LoRA...")
        model = prepare_model(config)

        callbacks = []

        if progress_callback is not None or should_stop_callback is not None:
            logger.info("Training callbacks configured (progress=%s, should_stop=%s)", bool(progress_callback), bool(should_stop_callback))

            callbacks.append(
                TrainingProgressCallback(
                    on_progress=progress_callback,
                    should_stop=should_stop_callback,
                    start_pct=20,
                    end_pct=95,
                )
            )
        else:
            logger.warning("Training progress/cancellation callbacks NOT PROVIDED")

        logger.info("Executing training for %d examples...", len(train_dataset))
        result = train_model(model, tokenizer, train_dataset, config, callbacks=callbacks)

        return result.to_dict()