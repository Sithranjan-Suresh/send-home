from fastapi.testclient import TestClient

from backend.app import app
from backend.report import build_report, parse_report

SAMPLE = """_Run on 2026-10-26 with `m` (temperature 0)._

| Sheet | Medicines found | Dose correct | Red-flag keywords | Follow-up keywords | Items flagged | Grade (orig → plain) |
|---|---|---|---|---|---|---|
| pneumonia.txt | 4/4 | 4/4 | 9/9 | 2/2 | 1/20 | 11.8 → 8.6 |
| **Total** | **19/19** | **18/19** | **37/37** | **12/12** | **2/91** | |

**Misses:**
- `eval_5.txt`: dose mismatch for amlodipine

**Grounded Q&A:** 12/12 questions handled correctly
"""


def test_parse():
    r = parse_report(SAMPLE)
    assert r["rows"][0]["sheet"] == "pneumonia" and r["rows"][0]["grade_original"] == 11.8
    assert r["rows"][0]["grade_plain"] == 8.6
    assert r["total"]["doses"] == "18/19"
    assert len(r["misses"]) == 1 and r["qa"].startswith("12/12")


def test_no_misses():
    assert parse_report(SAMPLE.replace("**Misses:**", "**Misses:** none in this run."))["misses"] == []


def test_real_files_and_endpoint():
    rep = build_report()
    assert len(rep["final"]) == 3 and rep["earlier"]
    assert all(len(r["rows"]) == 5 and r["total"] for r in rep["final"])
    r = TestClient(app).get("/api/report")
    assert r.status_code == 200 and r.json()["final"][0]["total"]["medicines"]
