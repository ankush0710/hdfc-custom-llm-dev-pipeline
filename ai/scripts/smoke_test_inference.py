from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Allow execution as:
# python ai/scripts/smoke_test_inference.py
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ai.inference.generator import GenerationConfig, generate
from ai.inference.loader import ModelLoader


DEFAULT_MODEL = "Qwen/Qwen3-0.6B"
DEFAULT_PROMPT = (
    "In one concise paragraph, explain what a banking customer should "
    "do after losing a debit card."
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run one inference smoke test against the existing AI layer."
    )
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    args = parser.parse_args()

    print("AI INFERENCE SMOKE TEST")
    print("=" * 50)
    print(f"Model:  {args.model}")
    print(f"Device: {args.device}")

    try:
        loader = ModelLoader(
            model_name=args.model,
            device=args.device,
        )

        tokenizer, model, resolved = loader.load()

        config = GenerationConfig(
            max_new_tokens=64,
            temperature=0.2,
            top_p=0.9,
            do_sample=False,
            seed=42,
        )

        started = time.perf_counter()

        result = generate(
            tokenizer=tokenizer,
            model=model,
            prompt=args.prompt,
            model_name=args.model,
            device=resolved.device,
            generation_config=config,
        )

        wall_time = time.perf_counter() - started

        response = result.get("response", "").strip()

        if not response:
            print("Response: FAIL — empty response")
            return 1

        print(f"Response: {response}")
        print(f"Reported latency: {result['latency_seconds']:.4f}s")
        print(f"Wall time:        {wall_time:.4f}s")
        print(f"Resolved device:  {resolved.device}")
        print(f"Dtype:            {resolved.dtype}")
        print("=" * 50)
        print("Overall: PASS")

        return 0

    except Exception as exc:
        print("=" * 50)
        print("Overall: FAIL")
        print(f"Error: {type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())