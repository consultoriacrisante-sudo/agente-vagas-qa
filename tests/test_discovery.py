import src.discovery as discovery


def test_discovery_collects_jobs_and_survives_failed_source(monkeypatch):
    good_job = object()

    def good(_identifier):
        return [good_job]

    def broken(_identifier):
        raise RuntimeError("provider unavailable")

    monkeypatch.setitem(discovery.COLLECTORS, "greenhouse", good)
    monkeypatch.setitem(discovery.COLLECTORS, "lever", broken)

    jobs, stats = discovery.discover_jobs([
        {"provider": "greenhouse", "identifier": "company-a"},
        {"provider": "lever", "identifier": "company-b"},
        {"provider": "unknown", "identifier": "company-c"},
    ])

    assert jobs == [good_job]
    assert stats == {
        "sources": 3,
        "successful_sources": 1,
        "failed_sources": 2,
        "jobs_found": 1,
    }


def test_discovery_with_no_sources_is_safe():
    jobs, stats = discovery.discover_jobs([])
    assert jobs == []
    assert stats["jobs_found"] == 0
    assert stats["failed_sources"] == 0
