"""Approximate Flesch-Kincaid grade, computed locally.

grade = 0.39 * (words / sentences) + 11.8 * (syllables / words) - 15.59
Syllables are estimated by counting vowel groups, so the score is approximate.
"""
import re

from .schemas import Analysis


def count_syllables(word: str) -> int:
    w = re.sub(r"[^a-z]", "", word.lower())
    if not w:
        return 0
    groups = re.findall(r"[aeiouy]+", w)
    n = len(groups)
    if w.endswith("e") and not w.endswith(("le", "ee")) and n > 1:
        n -= 1
    return max(n, 1)


def flesch_kincaid_grade(text: str) -> float | None:
    words = re.findall(r"[A-Za-z][A-Za-z'’-]*", text)
    if not words:
        return None
    sentences = [s for s in re.split(r"[.!?\n]+", text) if re.search(r"[A-Za-z]", s)]
    n_sent = max(len(sentences), 1)
    syllables = sum(count_syllables(w) for w in words)
    grade = 0.39 * (len(words) / n_sent) + 11.8 * (syllables / len(words)) - 15.59
    return round(max(grade, 0.0), 1)


def plain_text_from_analysis(a: Analysis) -> str:
    """Plain-language output only (source quotes excluded)."""
    lines: list[str] = []
    for s in a.summary:
        lines.append(s.text.rstrip(".") + ".")
    for m in a.medications:
        parts = [m.name, m.dose, m.schedule, m.purpose]
        lines.append(" ".join(p for p in parts if p).rstrip(".") + ".")
    for r in a.red_flags:
        lines.append(r.text.rstrip(".") + ".")
    for f in a.follow_ups:
        lines.append(" ".join(p for p in [f.what, f.when] if p).rstrip(".") + ".")
    return "\n".join(lines)
