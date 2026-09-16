from src.remote_gate import validate_remote


def test_accepts_explicit_remote():
    result = validate_remote("QA Engineer", "Brazil - Remote", "This is a fully remote role.")
    assert result.accepted is True


def test_rejects_hybrid_even_when_remote_is_mentioned():
    result = validate_remote(
        "QA Engineer - Remote",
        "São Paulo",
        "Remote role, but employees work 2 days a week in the office. Hybrid model.",
    )
    assert result.accepted is False
    assert result.reason == "hybrid_or_onsite_evidence"


def test_rejects_without_remote_evidence():
    result = validate_remote("QA Analyst", "São Paulo", "Great quality engineering team.")
    assert result.accepted is False
    assert result.reason == "remote_not_confirmed"
