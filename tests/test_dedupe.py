from src.dedupe import canonical_url, job_fingerprint


def test_canonical_url_removes_tracking_query():
    assert canonical_url("HTTPS://Jobs.Example.com/role/123/?utm_source=x#apply") == "https://jobs.example.com/role/123"


def test_same_application_url_dedupes_across_sources():
    a = job_fingerprint("1", "Acme", "QA", "Brazil", "https://jobs.acme.com/qa?src=a", source="greenhouse")
    b = job_fingerprint("999", "Acme", "QA", "Remote", "https://jobs.acme.com/qa?src=b", source="aggregator")
    assert a == b


def test_equal_source_ids_from_different_sources_do_not_collide_without_url():
    a = job_fingerprint("123", "Acme", "QA", "Brazil", "", source="greenhouse")
    b = job_fingerprint("123", "Other", "QA", "Brazil", "", source="lever")
    assert a != b
