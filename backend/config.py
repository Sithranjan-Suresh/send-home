"""Settings and fixed strings. Every user-facing fixed message lives here, once."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
ALLOWED_ORIGIN = os.getenv("ALLOWED_ORIGIN", "http://localhost:8000")
LLM_MOCK = os.getenv("LLM_MOCK", "0") == "1"
WARM_SAMPLES = os.getenv("WARM_SAMPLES", "1") == "1"
RATE_LIMIT_PER_MIN = int(os.getenv("RATE_LIMIT_PER_MIN", "0"))  # 0 = off

MAX_CHARS = 8000
MAX_QUESTION_CHARS = 300
MAX_BODY_BYTES = 10 * 1024
LLM_TIMEOUT_S = 40
SIMILARITY_THRESHOLD = 0.85

REFUSAL_TEXT = "That isn't in your paperwork — ask your nurse."
DOSE_MISSING_MSG = "Dose not listed — confirm with your nurse."
QUOTE_NOT_FOUND_MSG = "Couldn't verify — confirm with your nurse."
NUMBER_MISMATCH_MSG = "Numbers here don't match the source — confirm with your nurse."
NOT_DISCHARGE_MSG = "This doesn't look like discharge instructions."
TRANSLATION_DISCLAIMER = (
    "Machine-generated translation, not reviewed by a person. "
    "Confirm with your care team or an interpreter."
)


def require_key() -> None:
    if not LLM_MOCK and not LLM_API_KEY:
        raise RuntimeError(
            "LLM_API_KEY is not set. Copy .env.example to .env and add your key."
        )
