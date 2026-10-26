_Run on 2026-10-26 with `openai/gpt-oss-120b` (temperature 0). 5 synthetic sheets, hand-labelled expectations. Not clinical validation._

| Sheet | Medicines found | Dose correct | Red-flag keywords | Follow-up keywords | Items flagged | Grade (orig → plain) |
|---|---|---|---|---|---|---|
| pneumonia.txt | 4/4 | 4/4 | 9/9 | 2/2 | 1/20 | 11.8 → 7.8 |
| heart_failure.txt | 4/4 | 4/4 | 9/9 | 3/3 | 2/22 | 10.3 → 6.4 |
| appendectomy.txt | 3/3 | 3/3 | 7/7 | 1/1 | 0/18 | 10.3 → 8.3 |
| eval_4.txt | 4/4 | 4/4 | 7/7 | 3/3 | 0/19 | 10.8 → 7.4 |
| eval_5.txt | 4/4 | 4/4 | 5/5 | 3/3 | 1/17 | 10.0 → 8.7 |
| **Total** | **19/19** | **19/19** | **37/37** | **12/12** | **4/96** | |

Schema-valid responses: 5/5.

**Misses:** none in this run.
