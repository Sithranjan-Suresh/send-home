"""Official-label lookup for a medicine, using the Anakin web-data API.

Only the generic medicine NAME ever leaves this server (never the patient's text). Anakin fetches
MedlinePlus (U.S. National Library of Medicine) pages; plain code then extracts a word-for-word
excerpt, so the excerpt is verifiable against the page. Works without an Anakin key on Anakin's
keyless free tier; set ANAKIN_API_KEY to use your own credits.
"""
import json
import re
import threading
import time
from datetime import date
from pathlib import Path

import httpx

from . import config

SCRAPE_URL = config.ANAKIN_BASE.rstrip("/") + "/v1/url-scraper/scrape"
INDEX_URL = "https://medlineplus.gov/druginfo/drug_{letter}a.html"
SOURCE = "MedlinePlus (U.S. National Library of Medicine)"
SAVED = Path(__file__).resolve().parent.parent / "samples" / "labels.json"

_NAME_OK = re.compile(r"^[A-Za-z][A-Za-z0-9 ,.'()/-]{1,60}$")
_LINK = re.compile(r"\[([^\]]+)\]\((https://medlineplus\.gov/druginfo/meds/a\d+\.html)\)")
_cache: dict = {}
_lock = threading.Lock()


class AnakinError(Exception):
    """Anakin (or the page it fetched) could not be reached or read."""


def scrape(url: str) -> str:
    """Return the page as markdown text via Anakin (backs off when the keyless tier rate-limits)."""
    headers = {"X-API-Key": config.ANAKIN_API_KEY} if config.ANAKIN_API_KEY else {}
    for attempt in range(3):
        try:
            r = httpx.post(SCRAPE_URL, json={"url": url}, headers=headers, timeout=60)
        except httpx.HTTPError as e:
            raise AnakinError("could not reach Anakin") from e
        if r.status_code == 429 and attempt < 2:
            try:
                wait = float(r.headers.get("retry-after") or r.headers.get("x-ratelimit-reset") or 15)
            except ValueError:
                wait = 15.0
            time.sleep(min(wait, 30) + 1)
            continue
        if r.status_code != 200:
            raise AnakinError(f"Anakin status {r.status_code}")
        data = r.json()
        if data.get("statusCode") and data["statusCode"] >= 400:
            raise AnakinError(f"page status {data['statusCode']}")
        md = data.get("markdown") or ""
        if not md:
            raise AnakinError("empty page")
        return md
    raise AnakinError("Anakin rate limited")


def valid_name(name: str) -> bool:
    return bool(name) and bool(_NAME_OK.match(name.strip()))


_DROP = {"and", "with", "the", "of", "succinate", "tartrate", "hydrochloride", "hcl", "sulfate", "citrate",
         "mesylate", "tablet", "tablets", "capsule", "capsules", "er", "xl", "sr", "extended", "release"}
_SYN = {"inhaler": "inhalation"}
# Non-oral forms: never chosen unless the medicine name itself asks for that form.
_OTHER_FORMS = {"injection", "intravenous", "topical", "ophthalmic", "otic", "nasal", "rectal", "vaginal",
                "transdermal", "cream", "ointment", "gel", "lotion", "patch", "irrigation", "implant",
                "intramuscular", "subcutaneous", "intrathecal", "epidural", "dental"}


def _tokens(s: str) -> set[str]:
    s = re.sub(r"\([^)]*\)", " ", s.lower())
    toks = {_SYN.get(t, t) for t in re.split(r"[^a-z0-9]+", s) if t}
    return {t for t in toks if t not in _DROP}


def _same(a: str, b: str) -> bool:
    """Same word, or the same word stem (clavulanate / clavulanic)."""
    if a == b:
        return True
    short = min(len(a), len(b))
    common = 0
    for x, y in zip(a, b):
        if x != y:
            break
        common += 1
    return short >= 6 and common >= max(6, short - 3)


def find_entry(name: str, index_md: str):
    """Best index entry: it must cover every word of the name; fewer extra words wins."""
    want = _tokens(name)
    best, best_score = None, 0.0
    if not want:
        return None
    for text, url in _LINK.findall(index_md):
        have = _tokens(text)
        if (have & _OTHER_FORMS) - want:
            continue
        if not all(any(_same(w, h) for h in have) for w in want):
            continue
        extra = sum(1 for h in have if not any(_same(w, h) for w in want))
        score = 1.0 - 0.08 * extra
        if score > best_score:
            best, best_score = (text, url), score
    return best


def _plain(md: str) -> str:
    md = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", md)
    md = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", md)
    return re.sub(r"[ \t]+", " ", md)


def _section(plain: str, heading: str) -> str | None:
    """Text under a heading (given as a regex); ends at the next question-style heading."""
    m = re.search(rf"^\s*#*\s*{heading}\s*$", plain, re.I | re.M)
    if not m:
        return None
    rest = plain[m.end():]
    nxt = re.search(r"^\s*#*\s*(?:Why|How|What|Other|Can|Does|If|Which)\b[^\n]*\?\s*$", rest, re.M)
    return (rest[:nxt.start()] if nxt else rest[:1500]).strip() or None


def _excerpt(section: str | None, max_chars: int, max_sentences: int) -> str | None:
    """First sentences of a section, copied exactly (a substring of the page text)."""
    if not section:
        return None
    para = next((p.strip() for p in section.split("\n") if len(p.strip()) > 20), None)
    if not para:
        return None
    sentences = re.findall(r".+?(?:[.!?](?=\s|$)|$)", para)
    out = ""
    for s in sentences[:max_sentences]:
        if out and len(out) + len(s) > max_chars:
            break
        out += s
    return out.strip() or None


def parse_drug_page(md: str) -> dict:
    plain = _plain(md)
    purpose = _excerpt(_section(plain, r"Why is this medic\w+ prescribed\?"), 260, 2)
    usage = _excerpt(_section(plain, r"How should this medic\w+ be used\?"), 420, 3)
    # Each excerpt is a verbatim piece of the page text, checked here rather than assumed.
    purpose = purpose if purpose and purpose in plain else None
    usage = usage if usage and usage in plain else None
    return {"purpose": purpose, "usage": usage}


def lookup(name: str) -> dict:
    """Official label excerpt for a medicine name. Cached in memory (public label text only)."""
    name = name.strip()
    if not valid_name(name):
        raise ValueError("bad name")
    key = " ".join(sorted(_tokens(name)))
    with _lock:
        if key in _cache:
            hit = dict(_cache[key])
            hit["cached"] = True
            return hit
    letter = name[0].upper()
    entry = find_entry(name, scrape(INDEX_URL.format(letter=letter)))
    result = {"query": name, "found": False, "source": SOURCE, "via": "Anakin",
              "fetched": date.today().isoformat(), "cached": False}
    if entry:
        matched, url = entry
        parsed = parse_drug_page(scrape(url))
        if parsed["usage"] or parsed["purpose"]:
            result.update(found=True, matched=matched, url=url, **parsed)
    with _lock:
        if len(_cache) < 500:  # bounded: public label text only
            _cache[key] = dict(result)
    return result


def load_saved() -> None:
    try:
        blob = json.loads(SAVED.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return
    for key, val in blob.get("labels", {}).items():
        _cache[key] = val


def save_cache() -> None:
    SAVED.write_text(json.dumps({"labels": _cache}, ensure_ascii=False, indent=1), encoding="utf-8")


load_saved()
