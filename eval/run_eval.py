"""Accuracy check on the 5 synthetic sheets, plus a grounded-Q&A refusal check.

Run from the repo root (needs LLM_API_KEY in .env):
    python eval/run_eval.py            # sheets + questions
    python eval/run_eval.py --no-ask   # sheets only
Writes eval/results.json and eval/results.md. Misses are listed, not hidden.
"""
import argparse
import json
import sys
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend import config, service  # noqa: E402
from backend.verify import extract_numbers  # noqa: E402

SHEETS = ["pneumonia.txt", "heart_failure.txt", "appendectomy.txt", "eval_4.txt", "eval_5.txt"]


def blob(item) -> str:
    d = item.model_dump()
    return " ".join(str(v) for k, v in d.items() if isinstance(v, str)).lower()


def eval_sheet(name: str, expected: dict) -> dict:
    text = (ROOT / "samples" / name).read_text(encoding="utf-8").replace("\r\n", "\n")
    out = {"sheet": name, "valid": False, "misses": []}
    try:
        res = service.analyze(text)
    except Exception as e:  # report, never hide
        out["error"] = f"{type(e).__name__}: {getattr(e, 'message', e)}"
        out["misses"].append(f"analysis failed: {out['error']}")
        return out
    out["valid"] = True
    a = res.analysis
    out["grades"] = res.grades.model_dump()

    meds = a.medications
    found = dose_ok = 0
    for exp in expected["medications"]:
        m = next((m for m in meds if exp["name_contains"] in m.name.lower()), None)
        if not m:
            out["misses"].append(f"medicine not found: {exp['name_contains']}")
            continue
        found += 1
        want = exp["dose_numbers"]
        if want is None:
            ok = m.dose is None
        else:
            ok = m.dose is not None and set(want) <= extract_numbers(m.dose)
        if ok:
            dose_ok += 1
        else:
            out["misses"].append(f"dose mismatch for {exp['name_contains']}: expected {want}, got {m.dose!r}")
    out["meds_expected"] = len(expected["medications"])
    out["meds_found"] = found
    out["dose_correct"] = dose_ok

    rf_text = " ".join(blob(r) for r in a.red_flags)
    rf_hit = 0
    for kw in expected["red_flags"]:
        if kw.lower() in rf_text:
            rf_hit += 1
        else:
            out["misses"].append(f"red flag keyword missing: {kw!r}")
    out["rf_expected"], out["rf_found"] = len(expected["red_flags"]), rf_hit

    fu_text = " ".join(blob(f) for f in a.follow_ups)
    fu_hit = 0
    for kw in expected["follow_ups"]:
        if kw.lower() in fu_text:
            fu_hit += 1
        else:
            out["misses"].append(f"follow-up keyword missing: {kw!r}")
    out["fu_expected"], out["fu_found"] = len(expected["follow_ups"]), fu_hit

    items = a.summary + a.medications + a.red_flags + a.follow_ups
    out["items"] = len(items)
    out["flagged"] = sum(1 for i in items if i.flags)
    out["quote_not_found"] = sum(1 for i in items if "quote_not_found" in i.flags)
    out["dose_missing_flags"] = sum(1 for m in meds if "dose_missing" in m.flags)
    return out


def eval_questions() -> dict:
    qs = json.loads((ROOT / "eval" / "questions.json").read_text(encoding="utf-8"))["questions"]
    rows, correct = [], 0
    for q in qs:
        text = (ROOT / "samples" / q["sheet"]).read_text(encoding="utf-8").replace("\r\n", "\n")
        try:
            r = service.ask(text, q["q"])
            got = r.in_document
            refusal_exact = (r.answer == config.REFUSAL_TEXT) if not got else None
        except Exception as e:
            got, refusal_exact = None, None
            print(f"  ask error: {e}", flush=True)
        ok = got == q["in_document"] and (q["in_document"] or refusal_exact)
        correct += bool(ok)
        rows.append({**q, "got_in_document": got, "ok": bool(ok)})
        print(f"  [{'ok' if ok else 'MISS'}] {q['q']}", flush=True)
    return {"correct": correct, "total": len(qs), "rows": rows}


def table(results: list[dict]) -> str:
    lines = ["| Sheet | Medicines found | Dose correct | Red-flag keywords | Follow-up keywords | Items flagged | Grade (orig → plain) |",
             "|---|---|---|---|---|---|---|"]
    tot = dict(me=0, mf=0, dc=0, re=0, rf=0, fe=0, ff=0, it=0, fl=0)
    for r in results:
        if not r["valid"]:
            lines.append(f"| {r['sheet']} | FAILED | | | | | |")
            continue
        g = r["grades"]
        lines.append(f"| {r['sheet']} | {r['meds_found']}/{r['meds_expected']} | {r['dose_correct']}/{r['meds_expected']} | "
                     f"{r['rf_found']}/{r['rf_expected']} | {r['fu_found']}/{r['fu_expected']} | {r['flagged']}/{r['items']} | "
                     f"{g['original']} → {g['plain']} |")
        for k, v in zip(tot, [r["meds_expected"], r["meds_found"], r["dose_correct"], r["rf_expected"], r["rf_found"],
                              r["fu_expected"], r["fu_found"], r["items"], r["flagged"]]):
            tot[k] += v
    lines.append(f"| **Total** | **{tot['mf']}/{tot['me']}** | **{tot['dc']}/{tot['me']}** | **{tot['rf']}/{tot['re']}** | "
                 f"**{tot['ff']}/{tot['fe']}** | **{tot['fl']}/{tot['it']}** | |")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-ask", action="store_true")
    args = ap.parse_args()
    expected = json.loads((ROOT / "eval" / "expected.json").read_text(encoding="utf-8"))
    results = []
    for name in SHEETS:
        print(f"Analyzing {name} ...", flush=True)
        t = time.time()
        results.append(eval_sheet(name, expected[name]))
        print(f"  done in {time.time() - t:.1f}s; misses: {len(results[-1]['misses'])}", flush=True)
    qa = None if args.no_ask else eval_questions()

    md = [f"_Run on {date.today().isoformat()} with `{config.LLM_MODEL}` (temperature 0). "
          "5 synthetic sheets, hand-labelled expectations. Not clinical validation._", "", table(results), ""]
    valid = sum(r["valid"] for r in results)
    md.append(f"Schema-valid responses: {valid}/{len(results)}.\n")
    misses = [(r["sheet"], m) for r in results for m in r["misses"]]
    md.append("**Misses:**" if misses else "**Misses:** none in this run.")
    md += [f"- `{s}`: {m}" for s, m in misses]
    if qa:
        md += ["", f"**Grounded Q&A:** {qa['correct']}/{qa['total']} questions handled correctly "
               f"({sum(1 for r in qa['rows'] if r['in_document'])} answerable, "
               f"{sum(1 for r in qa['rows'] if not r['in_document'])} not in the sheet → must refuse with the fixed text)."]
        md += [f"- MISS `{r['sheet']}`: “{r['q']}” expected in_document={r['in_document']}, got {r['got_in_document']}"
               for r in qa["rows"] if not r["ok"]]
    (ROOT / "eval" / "results.json").write_text(json.dumps({"sheets": results, "qa": qa}, indent=2), encoding="utf-8")
    (ROOT / "eval" / "results.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n" + "\n".join(md))


if __name__ == "__main__":
    main()
