from src.collectors.tavily import _looks_like_job_url, _source


def test_known_job_platform_urls_are_accepted():
    assert _looks_like_job_url("https://www.linkedin.com/jobs/view/123")
    assert _looks_like_job_url("https://boards.greenhouse.io/company/jobs/123")
    assert _looks_like_job_url("https://company.jobs.example.com/qa")


def test_non_job_and_invalid_urls_are_rejected():
    assert not _looks_like_job_url("https://example.com/blog/qa")
    assert not _looks_like_job_url("javascript:alert(1)")
    assert not _looks_like_job_url("")


def test_source_is_derived_from_url_host():
    assert _source("https://www.linkedin.com/jobs/view/123") == "linkedin"
    assert _source("https://jobs.lever.co/acme/123") == "lever"
