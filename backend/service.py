"""Analyze / ask / translate logic. No state is kept and no text is logged."""
import hashlib
import json
import re
import threading
import time
from pathlib import Path

from pydantic import ValidationError

from . import config, llm, prompts
from .readability import flesch_kincaid_grade, plain_text_from_analysis
from .schemas import (Analysis, AnalyzeResponse, AskResponse, Grades, Span,
                      TranslateResponse)
from .verify import extract_numbers, locate_quote, verify_analysis

LANGUAGES = {"es": "Spanish"}

# Results for the three built-in synthetic samples are kept in memory so the demo is instant and
# stays inside the free-tier token limit. User-pasted text is never cached or stored.
SAMPLE_FILES = ["pneumonia", "heart_failure", "appendectomy"]
CHIP_QUESTIONS = ["When do I see my doctor?", "Can I take ibuprofen too?"]
_SAMPLES = {}
_cache: dict = {}
_translate_ok: set = set()
_lock = threading.Lock()


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _load_samples() -> None:
    root = Path(__file__).resolve().parent.parent / "samples"
    for name in SAMPLE_FILES:
        try:
            _SAMPLES[_sha((root / f"{name}.txt").read_text(encoding="utf-8"))] = name
        except OSError:
            pass


_load_samples()


class UserError(Exception):
    """An error with a message that is safe to show the user."""

    def __init__(self, code: str, message: str, status: int = 400):
        super().__init__(message)
        self.code, self.message, self.status = code, message, status


def _llm_json(system: str, user: str, validate=None) -> dict:
    """Call the model; retry once if the output is not valid JSON / schema."""
    last: Exception | None = None
    for _ in range(2):
        try:
            obj = llm.parse_json_strict(llm.call_llm(system, user))
            if validate:
                validate(obj)
            return obj
        except (llm.LLMBadOutput, ValidationError) as e:
            last = e
    raise UserError("bad_model_output",
                    "The AI returned an answer we couldn't read. Please try again.", 502) from last


def check_text(text: str) -> str:
    if not text or not text.strip():
        raise UserError("empty_input", "Paste or pick a discharge sheet first.")
    if len(text) > config.MAX_CHARS:
        raise UserError("too_long",
                        f"That's too long ({len(text):,} characters). The limit is {config.MAX_CHARS:,}.")
    return text


_EN_WORDS = {"the", "and", "to", "of", "a", "in", "for", "you", "your", "if", "or", "with", "is",
             "take", "call", "are", "on", "be", "at", "by", "as", "not", "do", "may", "have"}


def looks_english(text: str) -> bool:
    """Cheap guard: English paperwork is full of common function words."""
    words = re.findall(r"[a-z']+", text.lower())
    if len(words) < 15:
        return True  # too short to judge
    return sum(w in _EN_WORDS for w in words) / len(words) >= 0.08


def analyze(text: str) -> AnalyzeResponse:
    check_text(text)
    if not looks_english(text):
        raise UserError("not_english", "Sendhome reads English paperwork only for now.")
    key = ("analyze", _sha(text))
    is_sample = key[1] in _SAMPLES
    if is_sample and key in _cache:
        return _cache[key].model_copy(deep=True)
    obj = _llm_json(prompts.ANALYZE_SYSTEM, prompts.analyze_user(text),
                    validate=lambda o: Analysis(**o))
    analysis = Analysis(**obj)
    if not analysis.is_discharge_doc:
        return AnalyzeResponse(analysis=Analysis(is_discharge_doc=False), grades=Grades(),
                               message=config.NOT_DISCHARGE_MSG)
    analysis.summary = analysis.summary[:5]
    verify_analysis(text, analysis)
    grades = Grades(original=flesch_kincaid_grade(text),
                    plain=flesch_kincaid_grade(plain_text_from_analysis(analysis)))
    resp = AnalyzeResponse(analysis=analysis, grades=grades)
    if is_sample:
        _cache[key] = resp.model_copy(deep=True)
        _translate_ok.add(_sha(json.dumps(_translatable(analysis), sort_keys=True)))
    return resp


def ask(text: str, question: str) -> AskResponse:
    check_text(text)
    question = (question or "").strip()
    if not question:
        raise UserError("empty_question", "Type a question first.")
    if len(question) > config.MAX_QUESTION_CHARS:
        raise UserError("question_too_long",
                        f"Please keep the question under {config.MAX_QUESTION_CHARS} characters.")
    key = ("ask", _sha(text), question.lower())
    is_sample = key[1] in _SAMPLES
    if is_sample and key in _cache:
        return _cache[key].model_copy(deep=True)
    resp = _ask_uncached(text, question)
    if is_sample and len(_cache) < 300:
        _cache[key] = resp.model_copy(deep=True)
    return resp


def _ask_uncached(text: str, question: str) -> AskResponse:
    obj = _llm_json(prompts.ASK_SYSTEM, prompts.ask_user(text, question))
    refusal = AskResponse(in_document=False, answer=config.REFUSAL_TEXT)
    if obj.get("in_document") is not True or not isinstance(obj.get("answer"), str) \
            or not obj["answer"].strip():
        return refusal
    quotes, spans = [], []
    for q in obj.get("source_quotes") or []:
        if not isinstance(q, str):
            continue
        span, _, _ = locate_quote(text, q)
        if span:
            quotes.append(q)
            spans.append(span)
    if not spans:  # an answer with no verifiable source is treated as out-of-document
        return refusal
    return AskResponse(in_document=True, answer=obj["answer"].strip(),
                       source_quotes=quotes, spans=spans)


def _translatable(a: Analysis) -> dict:
    return {
        "summary": [s.text for s in a.summary],
        "medications": [{"name": m.name, "dose": m.dose, "schedule": m.schedule,
                         "purpose": m.purpose} for m in a.medications],
        "red_flags": [{"text": r.text, "urgency": r.urgency} for r in a.red_flags],
        "follow_ups": [{"what": f.what, "when": f.when} for f in a.follow_ups],
    }


def _strings(o) -> list[str]:
    if isinstance(o, str):
        return [o]
    if isinstance(o, dict):
        return [s for k, v in o.items() if k != "urgency" for s in _strings(v)]
    if isinstance(o, list):
        return [s for v in o for s in _strings(v)]
    return []


def _same_shape(a, b) -> bool:
    if isinstance(a, dict):
        return isinstance(b, dict) and a.keys() == b.keys() and all(_same_shape(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return isinstance(b, list) and len(a) == len(b) and all(_same_shape(x, y) for x, y in zip(a, b))
    return True


def translate(analysis: Analysis, language: str = "es") -> TranslateResponse:
    if language not in LANGUAGES:
        raise UserError("bad_language", "That language isn't supported yet.")
    name = LANGUAGES[language]
    source = _translatable(analysis)
    tkey = ("translate", language, _sha(json.dumps(source, sort_keys=True)))
    cacheable = tkey[2] in _translate_ok
    if cacheable and tkey in _cache:
        return _cache[tkey].model_copy(deep=True)

    def shaped(o):
        if not _same_shape(source, o):
            raise llm.LLMBadOutput("translation changed the structure")

    translated = _llm_json(prompts.TRANSLATE_SYSTEM.format(language=name),
                           prompts.translate_user(json.dumps(source, ensure_ascii=False)), shaped)
    # The back-translation sees ONLY the translated text, never the English original.
    back = _llm_json(prompts.BACKTRANSLATE_SYSTEM.format(language=name),
                     prompts.backtranslate_user(json.dumps(translated, ensure_ascii=False)), shaped)

    warnings = number_warnings(source, translated)
    low = " ".join(_strings(translated)).lower()
    for m in analysis.medications:
        if m.name and m.name.lower() not in low:
            warnings.append(f"The medicine name “{m.name}” does not appear in the translation.")
    resp = TranslateResponse(translated=translated, back_translation=back,
                             warnings=warnings, disclaimer=config.TRANSLATION_DISCLAIMER)
    if cacheable:
        _cache[tkey] = resp.model_copy(deep=True)
    return resp


def number_warnings(source: dict, translated: dict) -> list[str]:
    src = extract_numbers(" ".join(_strings(source)))
    tr = extract_numbers(" ".join(_strings(translated)))
    out = []
    for n in sorted(src - tr, key=float):
        out.append(f"The number {n} is in the original but not in the translation.")
    for n in sorted(tr - src, key=float):
        out.append(f"The number {n} is in the translation but not in the original.")
    return out


def warm_samples(pause: float = 22.0) -> None:
    """Pre-compute the built-in samples slowly (free tier is ~8k tokens/minute). Safe to fail."""
    root = Path(__file__).resolve().parent.parent / "samples"
    for name in SAMPLE_FILES:
        text = (root / f"{name}.txt").read_text(encoding="utf-8")
        for step in [lambda: analyze(text)] + [(lambda q=q: ask(text, q)) for q in CHIP_QUESTIONS]:
            try:
                step()
            except Exception:
                pass
            time.sleep(pause)
