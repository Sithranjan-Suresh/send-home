from fastapi.testclient import TestClient

from backend import anakin
from backend.app import app

INDEX = ("[Metoprolol](https://medlineplus.gov/druginfo/meds/a682864.html) "
         "[Metoprolol and Hydrochlorothiazide](https://medlineplus.gov/druginfo/meds/a601.html) "
         "[Albuterol](https://medlineplus.gov/druginfo/meds/a1.html) "
         "[Albuterol Oral Inhalation](https://medlineplus.gov/druginfo/meds/a2.html) "
         "[Amoxicillin](https://medlineplus.gov/druginfo/meds/a4.html) "
         "[Amoxicillin and Clavulanic Acid](https://medlineplus.gov/druginfo/meds/a5.html)")

PAGE = """# Metoprolol

Why is this medicine prescribed?

Metoprolol is used to treat high blood pressure and [chest pain](https://example.org/x). It also helps prevent heart attacks.

How should this medicine be used?

Metoprolol comes as a tablet to take by mouth. Take the regular tablet once or twice a day with meals. Take it around the same time every day. A fourth sentence that must not appear.

Other uses for this medicine

Something else.
"""


def fake_scrape(monkeypatch, calls):
    def _scrape(url):
        calls.append(url)
        return INDEX if "drug_" in url else PAGE
    monkeypatch.setattr(anakin, "scrape", _scrape)
    anakin._cache.clear()


def test_name_matching():
    f = anakin.find_entry
    assert f("Metoprolol succinate", INDEX)[0] == "Metoprolol"
    assert f("Albuterol inhaler", INDEX)[0] == "Albuterol Oral Inhalation"
    assert f("Albuterol", INDEX)[0] == "Albuterol"
    assert f("Amoxicillin-clavulanate", INDEX)[0] == "Amoxicillin and Clavulanic Acid"
    assert f("Amoxicillin", INDEX)[0] == "Amoxicillin"  # never the combination product
    assert f("Zorbaxin", INDEX) is None


def test_excerpts_are_verbatim_and_trimmed():
    out = anakin.parse_drug_page(PAGE)
    plain = anakin._plain(PAGE)
    assert out["purpose"] in plain and out["usage"] in plain
    assert "chest pain" in out["purpose"] and "example.org" not in out["purpose"]
    assert out["usage"].startswith("Metoprolol comes as a tablet")
    assert "fourth sentence" not in out["usage"]


def test_lookup_found_cached_and_only_name_used(monkeypatch):
    calls = []
    fake_scrape(monkeypatch, calls)
    r = anakin.lookup("Metoprolol succinate")
    assert r["found"] and r["matched"] == "Metoprolol" and r["via"] == "Anakin"
    assert r["url"].endswith("a682864.html") and not r["cached"]
    assert all(c.startswith("https://medlineplus.gov/") for c in calls) and len(calls) == 2
    assert anakin.lookup("metoprolol succinate")["cached"] and len(calls) == 2


def test_lookup_not_found(monkeypatch):
    fake_scrape(monkeypatch, [])
    assert anakin.lookup("Zorbaxin")["found"] is False


def test_name_validation():
    assert anakin.valid_name("Amoxicillin-clavulanate")
    for bad in ["", "x", "<script>", "Take 5 mg; DROP TABLE", "a" * 80]:
        assert not anakin.valid_name(bad)


def test_label_endpoint(monkeypatch):
    fake_scrape(monkeypatch, [])
    c = TestClient(app)
    ok = c.get("/api/label", params={"name": "Metoprolol"}).json()
    assert ok["found"] and ok["usage"]
    assert c.get("/api/label", params={"name": "<b>"}).status_code == 400


def test_label_endpoint_reports_anakin_failure(monkeypatch):
    def boom(url):
        raise anakin.AnakinError("down")
    monkeypatch.setattr(anakin, "scrape", boom)
    anakin._cache.clear()
    r = TestClient(app, raise_server_exceptions=False).get("/api/label", params={"name": "Metoprolol"})
    assert r.status_code == 502 and r.json()["error"] == "label_unavailable"


def test_non_oral_forms_are_skipped_unless_asked():
    idx = ("[Potassium Chloride Injection](https://medlineplus.gov/druginfo/meds/a9.html) "
           "[Lidocaine Topical](https://medlineplus.gov/druginfo/meds/a8.html)")
    assert anakin.find_entry("Potassium chloride", idx) is None
    assert anakin.find_entry("Potassium chloride injection", idx)[0] == "Potassium Chloride Injection"
    assert anakin.find_entry("Lidocaine", idx) is None
