import src.discovery as discovery


def test_discovery_collects_jobs_and_survives_failed_source(monkeypatch):
    good_job = object()

    def good(_identifier):
        return [good_job]

    def broken(_identifier):
        raise RuntimeError("provider unavailable")

    monkeypatch.setitem(discovery.COLLECTORS, "greenhouse", good)
    monkeypatch.setitem(discovery.COLLECTORS, "lever", broken)
    monkeypatch.setattr(discovery, "search_jobs", lambda: [])

    jobs, stats = discovery.discover_jobs([
        {"provider": "greenhouse", "identifier": "company-a"},
        {"provider": "lever", "identifier": "company-b"},
        {"provider": "unknown", "identifier": "company-c"},
    ])

    assert jobs == [good_job]
    assert stats["sources"] == 3
    assert stats["successful_sources"] == 1
    assert stats["failed_sources"] == 2
    assert stats["search_jobs"] == 0
    assert stats["search_failed"] is False
    assert stats["jobs_found"] == 1


def test_discovery_combines_search_results(monkeypatch):
    search_job = object()
    monkeypatch.setattr(discovery, "search_jobs", lambda: [search_job])
    jobs, stats = discovery.discover_jobs([])
    assert jobs == [search_job]
    assert stats["search_jobs"] == 1
    assert stats["jobs_found"] == 1


def test_search_failure_does_not_abort_daily_discovery(monkeypatch):
    def broken_search():
        raise RuntimeError("search unavailable")

    monkeypatch.setattr(discovery, "search_jobs", broken_search)
    jobs, stats = discovery.discover_jobs([])
    assert jobs == []
    assert stats["search_failed"] is True
    assert stats["jobs_found"] == 0
