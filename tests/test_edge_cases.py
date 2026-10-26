import glob

from fastapi.testclient import TestClient

from backend.app import app
from backend.schemas import Analysis
from backend.service import looks_english
from backend.verify import locate_quote, verify_analysis

client = TestClient(app, raise_server_exceptions=False)


def test_spanish_input_rejected_cleanly():
    es = ("Instrucciones de alta: Tome amoxicilina 500 mg cada 8 horas por 7 dias. "
          "Regrese a la sala de emergencias si tiene dificultad para respirar. Cita con su medico en 1 semana.")
    r = client.post("/api/analyze", json={"text": es})
    assert r.status_code == 400 and r.json()["error"] == "not_english"


def test_all_samples_look_english():
    for f in glob.glob("samples/*.txt") + glob.glob("tests/fixtures/*.txt"):
        assert looks_english(open(f, encoding="utf-8").read()), f


def test_unicode_quote_matches_original_offsets():
    doc = "Dose: ½ tablet at 98.6°F — take “with food”."
    span, kind, _ = locate_quote(doc, 'Dose: ½ tablet at 98.6°F - take "with food".')
    assert span is not None and doc[span.start:span.end] == doc


def test_windows_line_endings_roundtrip():
    doc = "A.\r\n\r\nTake  aspirin\r\n81 mg daily.\r\nEnd."
    span, _, _ = locate_quote(doc, "Take aspirin 81 mg daily.")
    assert span is not None
    assert doc[span.start:span.end].replace("\r\n", " ").replace("  ", " ") == "Take aspirin 81 mg daily."


def test_very_long_single_sentence_is_fast_and_correct():
    filler = "word " * 1500
    doc = filler + "Take ibuprofen 400 mg every 8 hours. " + filler
    span, kind, _ = locate_quote(doc, "Take ibuprofen 400 mg every 8 hours.")
    assert kind == "exact" and doc[span.start:span.end].startswith("Take ibuprofen")


def test_empty_quote_flagged_not_crashing():
    a = Analysis(summary=[{"text": "x", "source_quote": ""}])
    a = verify_analysis("some text", a)
    assert a.summary[0].flags == ["quote_not_found"]


def test_html_in_text_is_just_text_in_api_response(monkeypatch):
    from backend import llm
    import json

    evil = "<img src=x onerror=alert(1)>"
    reply = {"is_discharge_doc": True,
             "summary": [{"text": evil, "source_quote": evil}],
             "medications": [], "red_flags": [], "follow_ups": []}
    monkeypatch.setattr(llm, "call_llm", lambda *a, **k: json.dumps(reply))
    r = client.post("/api/analyze", json={"text": "Take pills. " + evil + " Go home."})
    assert r.status_code == 200
    item = r.json()["analysis"]["summary"][0]
    assert item["text"] == evil and item["span"] is not None  # returned as data; UI uses textContent
