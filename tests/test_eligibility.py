from src.eligibility import evaluate
from src.models import Job


def make_job(location: str, description: str = "100% remote") -> Job:
    return Job("test", "1", "QA Engineer", "Acme", location, description, "https://example.com/job")


def test_brazil_has_highest_priority():
    result = evaluate(make_job("Remote - Brazil"))
    assert result.accepted
    assert result.market == "brazil"
    assert result.priority == 100


def test_latam_is_valid_international():
    result = evaluate(make_job("LATAM Remote"))
    assert result.accepted
    assert result.market == "international"


def test_us_only_is_rejected_for_brazil_candidate():
    result = evaluate(make_job("Remote", "Remote - US only"))
    assert not result.accepted
    assert result.reason == "remote_not_eligible_from_brazil"
