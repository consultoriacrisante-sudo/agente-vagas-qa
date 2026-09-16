from src.url_gate import valid_application_url


def test_accepts_https_job_url():
    assert valid_application_url("https://jobs.example.com/job/123")


def test_rejects_missing_or_non_http_url():
    assert not valid_application_url("")
    assert not valid_application_url("jobs.example.com/job/123")
    assert not valid_application_url("javascript:alert(1)")
