"""
ai/inference/baseline.py

Command-line baseline inference / benchmarking tool.

Usage
-----
Run from the project root (C:\\Projects\\hdfc-custom-llm-pipeline) with the
virtual environment activated:

    python -m ai.inference.baseline --model Qwen/Qwen3-0.6B

Selecting a model:
    --model <hf_identifier>   e.g. Qwen/Qwen2.5-1.5B-Instruct
    If omitted, the tool looks for a `default_model` (or `model_name` /
    `model`) entry in ai/config/model_config.yaml. If neither is
    available, it exits with a clear error. No model name is ever
    hardcoded in this file.

Selecting CPU/GPU:
    --device auto|cuda|cpu    (default: auto -> prefers GPU if available)

Benchmark artifacts:
    Saved as JSON under ai/artifacts/ by default (override with --output).
    Each artifact records the prompt, response, generation config,
    latency, and GPU memory metrics so a later fine-tuned model run can be
    compared against this baseline.

Examples
--------
    python -m ai.inference.baseline --model Qwen/Qwen3-0.6B --device cpu
    python -m ai.inference.baseline --model Qwen/Qwen2.5-1.5B-Instruct ^
        --max-new-tokens 128 --output ai/artifacts/qwen25_run1.json
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import torch

from ai.inference.generator import GenerationConfig, generate
from ai.inference.loader import ModelLoadError, ModelLoader

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "ai" / "config" / "model_config.yaml"
DEFAULT_ARTIFACTS_DIR = PROJECT_ROOT / "ai" / "artifacts"
DEFAULT_PROMPT = "Explain in two sentences what a savings account is."


def _read_default_model_name(config_path: Path) -> Optional[str]:
    """
    Best-effort read of a default model name from model_config.yaml.

    This is a read-only helper: it never creates, modifies, or validates
    the config/registry files owned by other parts of the project. If the
    file is missing, unparsable, or lacks a recognizable key, it returns
    None so the caller can require an explicit --model argument instead.
    """
    if not config_path.exists():
        return None

    try:
        import yaml  # local import: only needed for this optional helper

        with config_path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
    except Exception as exc:  # noqa: BLE001 - config reading is best-effort
        logger.warning("Could not parse %s: %s", config_path, exc)
        return None

    if not isinstance(data, dict):
        return None

    for key in ("default_model", "model_name", "model"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    return None


def _gpu_memory_snapshot() -> Dict[str, Any]:
    """Return current GPU allocation stats, or {} on CPU-only systems."""
    if not torch.cuda.is_available():
        return {}
    return {
        "gpu_allocated_mb": round(torch.cuda.memory_allocated() / (1024 ** 2), 2),
        "gpu_reserved_mb": round(torch.cuda.memory_reserved() / (1024 ** 2), 2),
    }


def _gpu_static_info() -> Dict[str, Any]:
    """Return static GPU info (name, total memory), or Nones on CPU-only systems."""
    if not torch.cuda.is_available():
        return {"gpu_name": None, "gpu_memory_gb": None}
    props = torch.cuda.get_device_properties(0)
    return {
        "gpu_name": props.name,
        "gpu_memory_gb": round(props.total_memory / (1024 ** 3), 2),
    }


@dataclass
class BenchmarkArtifact:
    """Structured record saved as a JSON benchmark artifact."""

    timestamp: str
    model_name: str
    device: str
    torch_version: str
    cuda_version: Optional[str]
    gpu_name: Optional[str]
    gpu_memory_gb: Optional[float]
    prompt: str
    response: str
    generation_config: Dict[str, Any]
    latency_seconds: float
    memory_metrics: Dict[str, Any]
    seed: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "model_name": self.model_name,
            "device": self.device,
            "torch_version": self.torch_version,
            "cuda_version": self.cuda_version,
            "gpu_name": self.gpu_name,
            "gpu_memory_gb": self.gpu_memory_gb,
            "prompt": self.prompt,
            "response": self.response,
            "generation_config": self.generation_config,
            "latency_seconds": self.latency_seconds,
            "memory_metrics": self.memory_metrics,
            "seed": self.seed,
        }


def build_arg_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser for the baseline benchmark tool."""
    parser = argparse.ArgumentParser(
        prog="python -m ai.inference.baseline",
        description="Run a deterministic baseline inference benchmark.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help=(
            "Hugging Face model identifier (e.g. Qwen/Qwen3-0.6B). Falls "
            "back to a 'default_model' entry in ai/config/model_config.yaml "
            "if omitted."
        ),
    )
    parser.add_argument(
        "--device",
        type=str,
        default="auto",
        choices=["auto", "cuda", "cpu"],
        help="Device to run on (default: auto -> prefers GPU if available).",
    )
    parser.add_argument(
        "--prompt",
        type=str,
        default=DEFAULT_PROMPT,
        help="Prompt to run through the model.",
    )
    parser.add_argument(
        "--max-new-tokens", type=int, default=256, dest="max_new_tokens"
    )
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--top-p", type=float, default=0.9, dest="top_p")
    parser.add_argument(
        "--do-sample",
        action="store_true",
        default=False,
        dest="do_sample",
        help="Enable sampling. Default is off (deterministic greedy decoding).",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help=(
            "Path to write the JSON benchmark artifact. Defaults to "
            "ai/artifacts/<model>_<timestamp>.json"
        ),
    )
    parser.add_argument(
        "--config",
        type=str,
        default=str(DEFAULT_CONFIG_PATH),
        help="Path to model_config.yaml, used only to resolve a default model name.",
    )
    return parser


def _default_output_path(model_name: str) -> Path:
    """Build a default artifact path from the model name and a UTC timestamp."""
    safe_name = model_name.replace("/", "__")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return DEFAULT_ARTIFACTS_DIR / f"{safe_name}_{timestamp}.json"


def run(argv: Optional[List[str]] = None) -> int:
    """
    Entry point: parse args, run the benchmark, save the artifact, and
    print a human-readable summary.

    Returns
    -------
    int
        Process exit code (0 on success, non-zero on failure).
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    parser = build_arg_parser()
    args = parser.parse_args(argv)

    model_name = args.model or _read_default_model_name(Path(args.config))
    if not model_name:
        parser.error(
            "No model specified. Pass --model <hf_identifier> or set "
            "'default_model' in ai/config/model_config.yaml."
        )
        return 2  # argparse.error() exits; this line satisfies type checkers

    try:
        gen_config = GenerationConfig(
            max_new_tokens=args.max_new_tokens,
            temperature=args.temperature,
            top_p=args.top_p,
            do_sample=args.do_sample,
            seed=args.seed,
        )
    except ValueError as exc:
        parser.error(str(exc))
        return 2

    logger.info("Loading model '%s' (device=%s)...", model_name, args.device)
    try:
        loader = ModelLoader(model_name=model_name, device=args.device)
        tokenizer, model, resolved = loader.load()
    except ModelLoadError as exc:
        logger.error("Model loading failed: %s", exc)
        return 1

    mem_before = _gpu_memory_snapshot()
    if resolved.device == "cuda":
        torch.cuda.reset_peak_memory_stats()

    result = generate(
        tokenizer=tokenizer,
        model=model,
        prompt=args.prompt,
        model_name=model_name,
        device=resolved.device,
        generation_config=gen_config,
    )

    mem_after = _gpu_memory_snapshot()
    memory_metrics: Dict[str, Any] = {}
    if resolved.device == "cuda":
        memory_metrics = {
            "gpu_allocated_before_mb": mem_before.get("gpu_allocated_mb"),
            "gpu_allocated_after_mb": mem_after.get("gpu_allocated_mb"),
            "gpu_peak_allocated_mb": round(
                torch.cuda.max_memory_allocated() / (1024 ** 2), 2
            ),
            "gpu_reserved_after_mb": mem_after.get("gpu_reserved_mb"),
        }

    gpu_info = _gpu_static_info()
    artifact = BenchmarkArtifact(
        timestamp=datetime.now(timezone.utc).isoformat(),
        model_name=model_name,
        device=resolved.device,
        torch_version=torch.__version__,
        cuda_version=torch.version.cuda,
        gpu_name=gpu_info.get("gpu_name"),
        gpu_memory_gb=gpu_info.get("gpu_memory_gb"),
        prompt=result["prompt"],
        response=result["response"],
        generation_config=result["generation_config"],
        latency_seconds=result["latency_seconds"],
        memory_metrics=memory_metrics,
        seed=gen_config.seed,
    )

    output_path = (
        Path(args.output) if args.output else _default_output_path(model_name)
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(artifact.to_dict(), fh, indent=2)

    logger.info("Benchmark artifact saved to %s", output_path)

    print("\n=== Baseline Inference Summary ===")
    print(f"Model:        {model_name}")
    print(f"Device:       {resolved.device}")
    print(f"Latency:      {result['latency_seconds']}s")
    print(f"Prompt:       {args.prompt}")
    print(f"Response:     {result['response']}")
    if memory_metrics:
        print(f"GPU peak MB:  {memory_metrics.get('gpu_peak_allocated_mb')}")
    print(f"Artifact:     {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(run())