_Run on 2026-10-26 with `openai/gpt-oss-120b` (temperature 0). 5 synthetic sheets, hand-labelled expectations. Not clinical validation._

| Sheet | Medicines found | Dose correct | Red-flag keywords | Follow-up keywords | Items flagged | Grade (orig → plain) |
|---|---|---|---|---|---|---|
| pneumonia.txt | 4/4 | 4/4 | 9/9 | 2/2 | 1/20 | 11.8 → 8.6 |
| heart_failure.txt | 4/4 | 4/4 | 9/9 | 3/3 | 1/22 | 10.3 → 6.1 |
| appendectomy.txt | 3/3 | 3/3 | 7/7 | 1/1 | 0/18 | 10.3 → 8.4 |
| eval_4.txt | 4/4 | 4/4 | 7/7 | 3/3 | 0/14 | 10.8 → 9.1 |
| eval_5.txt | 4/4 | 3/4 | 5/5 | 3/3 | 0/17 | 10.0 → 7.5 |
| **Total** | **19/19** | **18/19** | **37/37** | **12/12** | **2/91** | |

Schema-valid responses: 5/5.

**Misses:**
- `eval_5.txt`: dose mismatch for amlodipine: expected None, got 'TAKE BY MOUTH EVERY DAY FOR BLOOD PRESSURE. THE DOSE WILL BE SET AT YOUR CLINIC VISIT.'

**Grounded Q&A:** 12/12 questions handled correctly (6 answerable, 6 not in the sheet → must refuse with the fixed text).
