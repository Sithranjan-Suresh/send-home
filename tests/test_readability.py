from backend.readability import count_syllables, flesch_kincaid_grade, plain_text_from_analysis
from backend.schemas import Analysis

EASY = "Take one pill. Drink water. Rest at home. Call us if you feel worse."
HARD = ("Postoperative anticoagulation therapy necessitates comprehensive monitoring of "
        "international normalized ratio values, notwithstanding contraindicated pharmacological interactions.")


def test_syllables():
    assert count_syllables("pill") == 1
    assert count_syllables("water") == 2
    assert count_syllables("medication") >= 4


def test_hard_scores_higher_than_easy():
    assert flesch_kincaid_grade(HARD) > flesch_kincaid_grade(EASY)


def test_empty_is_none():
    assert flesch_kincaid_grade("") is None
    assert flesch_kincaid_grade("123 456") is None


def test_plain_text_excludes_quotes():
    a = Analysis(summary=[{"text": "You had pneumonia", "source_quote": "SECRET_QUOTE"}])
    assert "SECRET_QUOTE" not in plain_text_from_analysis(a)
