_Run on 2026-10-26 with `openai/gpt-oss-120b` (temperature 0). 5 synthetic sheets, hand-labelled expectations. Not clinical validation._

| Sheet | Medicines found | Dose correct | Red-flag keywords | Follow-up keywords | Items flagged | Grade (orig → plain) |
|---|---|---|---|---|---|---|
| pneumonia.txt | 4/4 | 4/4 | 9/9 | 2/2 | 0/13 | 11.8 → 12.0 |
| heart_failure.txt | 4/4 | 4/4 | 9/9 | 3/3 | 1/14 | 10.3 → 8.5 |
| appendectomy.txt | 3/3 | 3/3 | 6/7 | 1/1 | 0/11 | 10.3 → 9.1 |
| eval_4.txt | 4/4 | 4/4 | 7/7 | 3/3 | 0/14 | 10.8 → 6.5 |
| eval_5.txt | 4/4 | 4/4 | 5/5 | 3/3 | 1/17 | 10.0 → 9.5 |
| **Total** | **19/19** | **19/19** | **36/37** | **12/12** | **2/69** | |

Schema-valid responses: 5/5.

**Misses:**
- `appendectomy.txt`: red flag keyword missing: 'bowel movement'

**Grounded Q&A:** 12/12 questions handled correctly (6 answerable, 6 not in the sheet → must refuse with the fixed text).
