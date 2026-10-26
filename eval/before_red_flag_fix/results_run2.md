_Run on 2026-10-26 with `openai/gpt-oss-120b` (temperature 0). 5 synthetic sheets, hand-labelled expectations. Not clinical validation._

| Sheet | Medicines found | Dose correct | Red-flag keywords | Follow-up keywords | Items flagged | Grade (orig → plain) |
|---|---|---|---|---|---|---|
| pneumonia.txt | 4/4 | 4/4 | 9/9 | 2/2 | 0/13 | 11.8 → 7.9 |
| heart_failure.txt | 4/4 | 4/4 | 9/9 | 3/3 | 1/14 | 10.3 → 9.3 |
| appendectomy.txt | 3/3 | 3/3 | 7/7 | 1/1 | 1/12 | 10.3 → 9.3 |
| eval_4.txt | 4/4 | 4/4 | 7/7 | 3/3 | 0/14 | 10.8 → 9.6 |
| eval_5.txt | 4/4 | 4/4 | 0/5 | 3/3 | 1/13 | 10.0 → 10.9 |
| **Total** | **19/19** | **19/19** | **32/37** | **12/12** | **3/66** | |

Schema-valid responses: 5/5.

**Misses:**
- `eval_5.txt`: red flag keyword missing: 'drooping'
- `eval_5.txt`: red flag keyword missing: 'weakness'
- `eval_5.txt`: red flag keyword missing: 'speaking'
- `eval_5.txt`: red flag keyword missing: 'headache'
- `eval_5.txt`: red flag keyword missing: 'bruising'
