"""Deterministic verification: the model proposes quotes, this code checks them.

Order of attempts for every source_quote:
  1. exact substring  2. normalized substring  3. best sentence (similarity)  4. not found
"""
import re
from difflib import SequenceMatcher

from . import config
from .schemas import Analysis, Span

_QUOTES = {"‘": "'", "’": "'", "‚": "'", "‛": "'",
           "“": '"', "”": '"', "„": '"'}
_DASHES = {"‐", "‑", "‒", "–", "—", "―", "−"}

# Words that end in a period without ending a sentence.
_ABBREV = {"dr", "mr", "mrs", "ms", "mg", "ml", "mcg", "vs", "e.g", "i.e", "approx",
           "no", "st", "tab", "tabs", "po", "bid", "tid", "qd", "oz", "lb", "lbs", "etc"}

_NOT_LISTED = {"", "not listed", "not stated", "not specified", "n/a", "na", "none",
               "unknown", "null", "not provided", "unspecified"}


def normalize(text: str) -> tuple[str, list[int]]:
    """Normalize for matching; return (string, map from normalized index to original index)."""
    out: list[str] = []
    idx: list[int] = []
    prev_space = True  # also trims leading whitespace
    for i, ch in enumerate(text):
        ch = _QUOTES.get(ch, ch)
        if ch in _DASHES:
            ch = "-"
        if ch.isspace() or ch == " ":
            if prev_space:
                continue
            out.append(" ")
            idx.append(i)
            prev_space = True
            continue
        prev_space = False
        for c in ch.lower():
            out.append(c)
            idx.append(i)
    if out and out[-1] == " ":
        out.pop()
        idx.pop()
    return "".join(out), idx


def split_sentences(text: str) -> list[tuple[int, int]]:
    """Return (start, end) offsets of sentences; text[start:end] is the exact slice."""
    spans: list[tuple[int, int]] = []
    start = 0
    n = len(text)
    i = 0
    while i < n:
        ch = text[i]
        boundary = False
        if ch == "\n":
            boundary = True
        elif ch in ".!?" and (i + 1 >= n or text[i + 1].isspace()):
            m = re.search(r"([A-Za-z0-9.]+)$", text[start:i])
            word = m.group(1).lower() if m else ""
            if ch == "." and (word in _ABBREV or word.isdigit()):
                boundary = False
            else:
                boundary = True
        i += 1
        if boundary:
            end = i if ch != "\n" else i - 1
            _push(spans, text, start, end)
            start = i
    _push(spans, text, start, n)
    return spans


def _push(spans: list[tuple[int, int]], text: str, start: int, end: int) -> None:
    seg = text[start:end]
    stripped = seg.strip()
    if not stripped:
        return
    lead = len(seg) - len(seg.lstrip())
    spans.append((start + lead, start + lead + len(stripped)))


def _find_all(hay: str, needle: str) -> list[int]:
    found, pos = [], hay.find(needle)
    while pos != -1:
        found.append(pos)
        pos = hay.find(needle, pos + 1)
    return found


def locate_quote(text: str, quote: str) -> tuple[Span | None, str, bool]:
    """Find quote in text. Returns (span, match_type, ambiguous)."""
    if not quote or not quote.strip():
        return None, "none", False
    q = quote.strip()

    ntext, idx = normalize(text)
    nq, _ = normalize(q)
    if nq:
        hits = _find_all(ntext, nq)
        if hits:
            s = idx[hits[0]]
            e = idx[hits[0] + len(nq) - 1] + 1
            kind = "exact" if text[s:e] == q else "normalized"
            return Span(start=s, end=e), kind, len(hits) > 1

    best, best_span = 0.0, None
    for s, e in split_sentences(text):
        ns, _ = normalize(text[s:e])
        ratio = SequenceMatcher(None, nq, ns).ratio()
        if ratio > best:
            best, best_span = ratio, (s, e)
    if best_span and best >= config.SIMILARITY_THRESHOLD:
        return Span(start=best_span[0], end=best_span[1]), "fuzzy", False
    return None, "none", False


def extract_numbers(s: str | None) -> set[str]:
    if not s:
        return set()
    s = re.sub(r"(?<=\d),(?=\d{3}\b)", "", s)
    return set(re.findall(r"\d+(?:\.\d+)?", s))


def clean_null(v: str | None) -> str | None:
    """Treat placeholder strings like 'not listed' as missing."""
    if v is None:
        return None
    return None if v.strip().lower().strip(".") in _NOT_LISTED else v


def _check(text: str, item) -> None:
    span, match_type, ambiguous = locate_quote(text, item.source_quote)
    item.span = span
    item.match = match_type if span else None
    item.flags = [f for f in item.flags if f not in ("quote_not_found", "ambiguous_match")]
    if span is None:
        item.flags.append("quote_not_found")
    elif ambiguous:
        item.flags.append("ambiguous_match")


def verify_analysis(text: str, analysis: Analysis) -> Analysis:
    """Attach span and flags to every item. Never drops an item. Safe to run again on its own output."""
    for group in (analysis.summary, analysis.medications, analysis.red_flags, analysis.follow_ups):
        for item in group:
            item.flags = []
            _check(text, item)
    for m in analysis.medications:
        m.dose = clean_null(m.dose)
        m.schedule = clean_null(m.schedule)
        m.purpose = clean_null(m.purpose)
        if m.dose is None:
            m.flags.append("dose_missing")
        quote_nums = extract_numbers(m.source_quote)
        if (extract_numbers(m.dose) | extract_numbers(m.schedule)) - quote_nums:
            m.flags.append("number_mismatch")
    for f in analysis.follow_ups:
        f.when = clean_null(f.when)
    return analysis
