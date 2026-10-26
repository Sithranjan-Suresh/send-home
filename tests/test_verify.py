from backend.schemas import Analysis
from backend.verify import (extract_numbers, locate_quote, normalize, split_sentences,
                            verify_analysis)

DOC = ("Discharge Summary\nTake amoxicillin 500 mg   by mouth three times a day for 7 days.\n"
       "Call your doctor if you have a fever above 101 F. Dr. Smith will see you in 2 weeks.\n"
       "Take amoxicillin 500 mg by mouth three times a day for 7 days.")


def test_normalize_maps_offsets():
    n, idx = normalize("A  B’s – x")
    assert n == "a b's - x"
    assert len(n) == len(idx)


def test_exact():
    q = "Call your doctor if you have a fever above 101 F."
    span, kind, amb = locate_quote(DOC, q)
    assert kind == "exact" and DOC[span.start:span.end] == q and not amb


def test_normalized_whitespace_and_case():
    span, kind, _ = locate_quote(DOC, "TAKE amoxicillin 500 mg by mouth three times a day")
    assert kind == "normalized"
    assert DOC[span.start:span.end].startswith("Take amoxicillin 500 mg   by mouth")


def test_curly_and_dash():
    doc = "Don’t drive – for 24 hours."
    span, kind, _ = locate_quote(doc, "Don't drive - for 24 hours.")
    assert kind == "normalized" and doc[span.start:span.end] == doc


def test_fuzzy_sentence():
    span, kind, _ = locate_quote(DOC, "Call your docter if you have a fevr above 101 F.")
    assert kind == "fuzzy" and "fever above 101" in DOC[span.start:span.end]


def test_unrelated_not_found():
    span, kind, _ = locate_quote(DOC, "Avoid grapefruit juice entirely.")
    assert span is None and kind == "none"


def test_duplicate_ambiguous():
    span, kind, amb = locate_quote(DOC, "Take amoxicillin 500 mg by mouth three times a day for 7 days.")
    assert amb and span.start > 0


def test_sentence_offsets_slice_back():
    sents = [DOC[s:e] for s, e in split_sentences(DOC)]
    assert all(x == x.strip() for x in sents)
    assert any(x.startswith("Dr. Smith will") or "Dr. Smith will" in x for x in sents)


def test_crlf_offsets():
    doc = "Line one.\r\nTake aspirin 81 mg daily.\r\nEnd."
    span, kind, _ = locate_quote(doc, "Take aspirin 81 mg daily.")
    assert doc[span.start:span.end] == "Take aspirin 81 mg daily."


def test_numbers():
    assert extract_numbers("5 mg twice a day") == {"5"}
    assert extract_numbers("0.5 mg for 10-14 days") == {"0.5", "10", "14"}
    assert extract_numbers("1,000 units") == {"1000"}


def _analysis(**med):
    base = {"name": "amoxicillin", "dose": "500 mg", "schedule": "three times a day",
            "source_quote": "Take amoxicillin 500 mg by mouth three times a day for 7 days."}
    base.update(med)
    return Analysis(medications=[base],
                    summary=[{"text": "s", "source_quote": "Discharge Summary"}])


def test_ok_med_links():
    a = verify_analysis(DOC, _analysis())
    assert a.medications[0].span is not None
    assert "quote_not_found" not in a.medications[0].flags


def test_dose_missing():
    a = verify_analysis(DOC, _analysis(dose=None))
    assert "dose_missing" in a.medications[0].flags
    a = verify_analysis(DOC, _analysis(dose="Not listed"))
    assert "dose_missing" in a.medications[0].flags


def test_number_mismatch():
    a = verify_analysis(DOC, _analysis(dose="250 mg"))
    assert "number_mismatch" in a.medications[0].flags


def test_corrupted_quote_flagged_and_item_kept():
    a = _analysis(source_quote="Take zorbaxin 900 mg with grapefruit every hour.")
    n_before = len(a.medications)
    a = verify_analysis(DOC, a)
    assert "quote_not_found" in a.medications[0].flags
    assert a.medications[0].span is None and len(a.medications) == n_before


def test_match_type_recorded():
    a = verify_analysis(DOC, Analysis(summary=[
        {"text": "a", "source_quote": "Discharge Summary"},
        {"text": "b", "source_quote": "TAKE amoxicillin 500 mg by mouth three times a day"},
        {"text": "c", "source_quote": "Call your docter if you have a fevr above 101 F."},
        {"text": "d", "source_quote": "Nothing like this appears."}]))
    assert [i.match for i in a.summary] == ["exact", "normalized", "fuzzy", None]


def test_reverify_is_idempotent_and_catches_tampering():
    a = verify_analysis(DOC, _analysis(dose=None))
    once = [list(m.flags) for m in a.medications]
    twice = [list(m.flags) for m in verify_analysis(DOC, a).medications]
    assert once == twice  # no duplicated flags on a second pass


def test_break_it_changes_are_caught():
    a = verify_analysis(DOC, _analysis())
    assert "number_mismatch" not in a.medications[0].flags
    a.medications[0].dose = "5000 mg"  # edit the dose, keep the real quote
    a.summary[0].source_quote = "Double your dose if you miss one."  # fabricate a quote
    a = verify_analysis(DOC, a)
    assert "number_mismatch" in a.medications[0].flags
    assert "quote_not_found" in a.summary[0].flags and a.summary[0].span is None
