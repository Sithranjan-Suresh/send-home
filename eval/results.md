_Run on 2026-10-26 with `openai/gpt-oss-120b` (temperature 0). 5 synthetic sheets, hand-labelled expectations. Not clinical validation._

| Sheet | Medicines found | Dose correct | Red-flag keywords | Follow-up keywords | Items flagged | Grade (orig → plain) |
|---|---|---|---|---|---|---|
| pneumonia.txt | 4/4 | 4/4 | 9/9 | 2/2 | 0/13 | 6.9 → 8.8 |
| heart_failure.txt | 4/4 | 4/4 | 9/9 | 3/3 | 2/14 | 4.7 → 6.9 |
| appendectomy.txt | 3/3 | 3/3 | 7/7 | 1/1 | 0/11 | 5.2 → 8.2 |
| eval_4.txt | 4/4 | 2/4 | 7/7 | 3/3 | 0/14 | 6.1 → 6.9 |
| eval_5.txt | 4/4 | 4/4 | 5/5 | 3/3 | 1/14 | 5.6 → 7.1 |
| **Total** | **19/19** | **17/19** | **37/37** | **12/12** | **3/66** | |

Schema-valid responses: 5/5.

**Misses:**
- `eval_4.txt`: dose mismatch for metformin: expected ['500'], got '1 tablet'
- `eval_4.txt`: dose mismatch for ciprofloxacin: expected ['500'], got '1 tablet'

**Grounded Q&A:** 12/12 questions handled correctly (6 answerable, 6 not in the sheet → must refuse with the fixed text).
