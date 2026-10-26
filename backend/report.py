"""Read the evaluation results already committed in eval/ and shape them for the Report page.

Nothing here is computed from user text; it only parses the saved markdown reports.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVAL = ROOT / "eval"

_COLS = ["sheet", "medicines", "doses", "red_flags", "follow_ups", "flagged", "grade"]


def _clean(cell: str) -> str:
    return cell.replace("*", "").strip()


def parse_report(md: str) -> dict:
    rows, total = [], None
    for line in md.splitlines():
        if not line.startswith("|") or set(line.replace("|", "").strip()) <= set("-: "):
            continue
        cells = [_clean(c) for c in line.strip().strip("|").split("|")]
        if len(cells) != len(_COLS) or cells[0] == "Sheet":
            continue
        row = dict(zip(_COLS, cells))
        grade = row["grade"]
        parts = [p.strip() for p in grade.split("\u2192")] if "\u2192" in grade else []
        row["grade_original"] = float(parts[0]) if len(parts) == 2 and parts[0] else None
        row["grade_plain"] = float(parts[1]) if len(parts) == 2 and parts[1] else None
        if row["sheet"].lower() == "total":
            total = row
        else:
            row["sheet"] = row["sheet"].replace(".txt", "")
            rows.append(row)
    misses = [m.group(1).strip() for m in re.finditer(r"^- (.+)$", md, re.M)]
    qa = re.search(r"\*\*Grounded Q&A:\*\*\s*(.+)", md)
    none_missed = "Misses:** none" in md
    header = re.search(r"^_Run on (.+?)_$", md, re.M)
    return {"rows": rows, "total": total, "misses": [] if none_missed else misses,
            "qa": qa.group(1).strip() if qa else None,
            "header": header.group(1) if header else None}


def _load(path: Path) -> dict | None:
    try:
        return parse_report(path.read_text(encoding="utf-8"))
    except OSError:
        return None


def build_report() -> dict:
    final = []
    for n in (1, 2, 3):
        r = _load(EVAL / f"results_run{n}.md")
        if r:
            final.append({"name": f"Run {n}", **r})
    earlier = []
    first = _load(EVAL / "first_run" / "results_first_run.md")
    if first:
        earlier.append({"name": "First run (plain-language samples)", **first,
                        "why": "Samples were too plainly written, so the reading grade went up "
                               "and two doses lost their strength. I rewrote the samples and tightened the dose prompt."})
    for n in (1, 2, 3):
        r = _load(EVAL / "before_red_flag_fix" / f"results_run{n}.md")
        if r:
            earlier.append({"name": f"Before the warning-sign fix, run {n}", **r,
                            "why": "The model sometimes dropped a whole group of warning signs. "
                                   "I added a completeness rule to the prompt."})
    return {"final": final, "earlier": earlier,
            "caveat": "Five synthetic sheets, expectations written by hand. A small self-check, not clinical validation."}
