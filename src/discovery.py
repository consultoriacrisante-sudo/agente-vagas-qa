import json
from pathlib import Path

from src.collectors.ashby import collect as collect_ashby
from src.collectors.greenhouse import collect as collect_greenhouse
from src.collectors.lever import collect as collect_lever
from src.collectors.smartrecruiters import collect as collect_smartrecruiters
from src.collectors.tavily import search_jobs
from src.models import Job

SOURCES_PATH = Path(__file__).resolve().parents[1] / "config" / "sources.json"
COLLECTORS = {
    "greenhouse": collect_greenhouse,
    "lever": collect_lever,
    "ashby": collect_ashby,
    "smartrecruiters": collect_smartrecruiters,
}


def load_sources(path: Path = SOURCES_PATH) -> list[dict]:
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [source for source in payload.get("sources", []) if source.get("enabled", True)]


def discover_jobs(sources: list[dict] | None = None) -> tuple[list[Job], dict]:
    """Combine configured official ATS boards with search discovery, isolating provider failures."""
    sources = load_sources() if sources is None else sources
    jobs: list[Job] = []
    stats = {
        "sources": len(sources), "successful_sources": 0, "failed_sources": 0,
        "search_jobs": 0, "search_failed": False, "jobs_found": 0,
    }

    for source in sources:
        provider = source.get("provider", "").lower()
        identifier = source.get("identifier", "").strip()
        collector = COLLECTORS.get(provider)
        if not collector or not identifier:
            stats["failed_sources"] += 1
            continue
        try:
            jobs.extend(collector(identifier))
            stats["successful_sources"] += 1
        except Exception:
            stats["failed_sources"] += 1

    try:
        discovered = search_jobs()
        jobs.extend(discovered)
        stats["search_jobs"] = len(discovered)
    except Exception:
        stats["search_failed"] = True

    stats["jobs_found"] = len(jobs)
    return jobs, stats
