import pytest

from src.models import Job
from src.telegram import format_job


def make_job(url="https://jobs.example.com/123"):
    return Job(
        source="test",
        source_id="123",
        title="Senior QA Engineer",
        company="Example",
        location="Brazil",
        description="Remote QA role",
        url=url,
        remote=True,
        employment_type="CLT",
        track="qa",
        match_score=91,
        matched_skills=["API", "Detox"],
    )


def test_format_job_contains_candidate_action_context():
    text = format_job(make_job())
    assert "Senior QA Engineer" in text
    assert "Match 91%" in text
    assert "100% REMOTO" in text
    assert "Candidatura" in text


@pytest.mark.parametrize("url", ["", "not-a-url", "ftp://jobs.example.com/123"])
def test_format_job_rejects_invalid_application_url(url):
    with pytest.raises(ValueError, match="URL válida"):
        format_job(make_job(url))
