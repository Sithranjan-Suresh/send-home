_Run on 2026-10-26 with `openai/gpt-oss-20b` (temperature 0). 5 synthetic sheets, hand-labelled expectations. Not clinical validation._

| Sheet | Medicines found | Dose correct | Red-flag keywords | Follow-up keywords | Items flagged | Grade (orig → plain) |
|---|---|---|---|---|---|---|
| pneumonia.txt | 4/4 | 4/4 | 9/9 | 2/2 | 1/18 | 11.8 → 8.9 |
| heart_failure.txt | 4/4 | 4/4 | 9/9 | 3/3 | 2/14 | 10.3 → 8.1 |
| appendectomy.txt | 3/3 | 3/3 | 7/7 | 1/1 | 0/12 | 10.3 → 9.4 |
| eval_4.txt | FAILED | | | | | |
| eval_5.txt | 4/4 | 4/4 | 5/5 | 3/3 | 1/12 | 10.0 → 6.8 |
| **Total** | **15/15** | **15/15** | **30/30** | **9/9** | **4/56** | |

Schema-valid responses: 4/5.

**Misses:**
- `eval_4.txt`: analysis failed: UserError: The AI returned an answer we couldn't read. Please try again.
