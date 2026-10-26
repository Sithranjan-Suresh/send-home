_Run on 2026-10-26 with `qwen/qwen3.8-27b` (temperature 0). 5 synthetic sheets, hand-labelled expectations. Not clinical validation._

| Sheet | Medicines found | Dose correct | Red-flag keywords | Follow-up keywords | Items flagged | Grade (orig → plain) |
|---|---|---|---|---|---|---|
| pneumonia.txt | 4/4 | 4/4 | 9/9 | 2/2 | 0/20 | 11.8 → 5.8 |
| heart_failure.txt | FAILED | | | | | |
| appendectomy.txt | 3/3 | 3/3 | 7/7 | 1/1 | 0/20 | 10.3 → 5.5 |
| eval_4.txt | FAILED | | | | | |
| eval_5.txt | FAILED | | | | | |
| **Total** | **7/7** | **7/7** | **16/16** | **3/3** | **0/40** | |

Schema-valid responses: 2/5.

**Misses:**
- `heart_failure.txt`: analysis failed: LLMRateLimited: rate limited
- `eval_4.txt`: analysis failed: LLMRateLimited: rate limited
- `eval_5.txt`: analysis failed: LLMRateLimited: rate limited
