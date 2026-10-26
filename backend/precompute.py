"""Build samples/precomputed.json from REAL runs on the three built-in samples.

    python -m backend.precompute

Slow on purpose (free-tier token limits). Only built-in sample text and its outputs are saved.
"""
import json
import sys
import time
from datetime import date

from . import config, llm, service


PAUSE = 25


def retry(fn, label: str):
    for attempt in range(8):
        try:
            out = fn()
            time.sleep(PAUSE)  # stay under the per-minute token limit
            return out
        except llm.LLMError as e:
            wait = 30 * (attempt + 1)
            print(f"  {label}: {type(e).__name__}, waiting {wait}s", flush=True)
            time.sleep(wait)
    raise SystemExit(f"gave up on {label}")


def main() -> None:
    config.LLM_FALLBACK_MODELS = []  # saved results must come from the main model
    root = service.PRECOMPUTED.parent
    models = set()
    for name in service.SAMPLE_FILES:
        text = (root / f"{name}.txt").read_text(encoding="utf-8")
        print(f"{name}: analyze", flush=True)
        res = retry(lambda: service.analyze(text), f"{name} analyze")
        for q in service.CHIP_QUESTIONS:
            print(f"{name}: ask {q!r}", flush=True)
            retry(lambda: service.ask(text, q), f"{name} ask")
        print(f"{name}: translate", flush=True)
        retry(lambda: service.translate(res.analysis, "es"), f"{name} translate")
    service.save_precomputed({"model": config.LLM_MODEL, "date": date.today().isoformat()})
    print("saved", service.PRECOMPUTED, len(service._cache), "entries")


if __name__ == "__main__":
    main()
