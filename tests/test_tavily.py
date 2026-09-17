import requests

from src.collectors.tavily import _looks_like_job_url, _source, search_jobs


def test_individual_job_urls_are_accepted():
    assert _looks_like_job_url("https://www.linkedin.com/jobs/view/123")
    assert _looks_like_job_url("https://www.indeed.com/viewjob?jk=abc123")
    assert _looks_like_job_url("https://www.glassdoor.com/job-listing/qa-engineer-acme-JV_IC.htm?jl=123")
    assert _looks_like_job_url("https://boards.greenhouse.io/company/jobs/123")
    assert _looks_like_job_url("https://jobs.lever.co/acme/123")
    assert _looks_like_job_url("https://jobs.ashbyhq.com/acme/123")
    assert _looks_like_job_url("https://careers.example.com/jobs/123")


def test_generic_job_search_and_invalid_urls_are_rejected():
    assert not _looks_like_job_url("https://www.linkedin.com/jobs/search/?keywords=QA")
    assert not _looks_like_job_url("https://www.indeed.com/jobs?q=QA")
    assert not _looks_like_job_url("https://www.glassdoor.com/Job/qa-jobs-SRCH.htm")
    assert not _looks_like_job_url("https://careers.example.com/")
    assert not _looks_like_job_url("https://example.com/blog/qa")
    assert not _looks_like_job_url("javascript:alert(1)")
    assert not _looks_like_job_url("")


def test_source_is_derived_from_url_host():
    assert _source("https://www.linkedin.com/jobs/view/123") == "linkedin"
    assert _source("https://jobs.lever.co/acme/123") == "lever"


class _Response:
    def __init__(self, payload=None, error=False):
        self.payload = payload or {"results": []}
        self.error = error

    def raise_for_status(self):
        if self.error:
            raise requests.HTTPError("temporary search failure")

    def json(self):
        return self.payload


def test_one_failed_query_does_not_abort_remaining_searches(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")
    responses = iter([
        _Response(error=True),
        _Response({"results": [{
            "url": "https://www.linkedin.com/jobs/view/123",
            "title": "QA Engineer",
            "content": "Remote Brazil QA automation role",
        }]}),
    ])
    monkeypatch.setattr("src.collectors.tavily.requests.post", lambda *args, **kwargs: next(responses))

    jobs = search_jobs(["first", "second"])

    assert len(jobs) == 1
    assert jobs[0].source == "linkedin"
    assert jobs[0].source_id
    assert jobs[0].url == "https://www.linkedin.com/jobs/view/123"
