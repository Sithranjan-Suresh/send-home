"""Save official-label lookups (via Anakin) for every medicine in the built-in samples.

    python -m backend.precompute_labels

Writes samples/labels.json: public MedlinePlus text only, no patient or pasted text.
"""
import time

from . import anakin, service


def main() -> None:
    names = []
    for key, resp in service._cache.items():
        if key[0] == "analyze":
            names += [m.name for m in resp.analysis.medications]
    for n in dict.fromkeys(names):
        for attempt in range(4):
            try:
                r = anakin.lookup(n)
                print(f"{n}: found={r['found']} matched={r.get('matched')}", flush=True)
                break
            except anakin.AnakinError as e:
                print(f"{n}: {e}; retrying", flush=True)
                time.sleep(20)
        time.sleep(3)
    anakin.save_cache()
    print("saved", len(anakin._cache), "labels")


if __name__ == "__main__":
    main()
