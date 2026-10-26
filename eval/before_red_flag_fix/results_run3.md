_Run on 2026-10-26 with `openai/gpt-oss-120b` (temperature 0). 5 synthetic sheets, hand-labelled expectations. Not clinical validation._

| Sheet | Medicines found | Dose correct | Red-flag keywords | Follow-up keywords | Items flagged | Grade (orig → plain) |
|---|---|---|---|---|---|---|
| pneumonia.txt | 4/4 | 4/4 | 9/9 | 2/2 | 0/13 | 11.8 → 12.0 |
| heart_failure.txt | 4/4 | 4/4 | 4/9 | 3/3 | 1/13 | 10.3 → 9.5 |
| appendectomy.txt | 3/3 | 3/3 | 7/7 | 1/1 | 0/11 | 10.3 → 9.7 |
| eval_4.txt | 4/4 | 4/4 | 7/7 | 3/3 | 0/14 | 10.8 → 6.3 |
| eval_5.txt | 4/4 | 4/4 | 5/5 | 3/3 | 1/17 | 10.0 → 7.8 |
| **Total** | **19/19** | **19/19** | **32/37** | **12/12** | **2/68** | |

Schema-valid responses: 5/5.

**Misses:**
- `heart_failure.txt`: red flag keyword missing: '3 pounds'
- `heart_failure.txt`: red flag keyword missing: 'swell'
- `heart_failure.txt`: red flag keyword missing: 'pillows'
- `heart_failure.txt`: red flag keyword missing: 'dizzy'
- `heart_failure.txt`: red flag keyword missing: 'dry cough'
