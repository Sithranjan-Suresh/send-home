"""Canned responses for LLM_MOCK=1 so the UI and tests run without API calls."""
import json


def respond(system: str, user: str) -> str:
    if "translate" in system.lower() and "plain english" in system.lower():
        return json.dumps({"summary": ["You had pneumonia."], "medications": [], "red_flags": [], "follow_ups": []})
    if "translate" in system.lower():
        return json.dumps({"summary": ["Usted tuvo neumonia."], "medications": [], "red_flags": [], "follow_ups": []})
    if "<question>" in user:
        return json.dumps({"in_document": False, "answer": None, "source_quotes": []})
    return json.dumps({
        "is_discharge_doc": True,
        "summary": [{"text": "You had pneumonia.", "source_quote": "Diagnosis: Community-acquired pneumonia"}],
        "medications": [], "red_flags": [], "follow_ups": [],
    })
