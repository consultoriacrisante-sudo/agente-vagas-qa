import json
from pathlib import Path

from src.collectors.ashby import collect as collect_ashby
from src.collectors.greenhouse import collect as collect_greenhouse
from src.collectors.lever import collect as collect_lever
from src.collectors.smartrecruiters import collect as collect_smartrecruiters
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
    """Collect configured official ATS boards without letting one source abort the run."""
    sources = load_sources() if sources is None else sources
    jobs: list[Job] = []
    stats = {"sources": len(sources), "successful_sources": 0, "failed_sources": 0, "jobs_found": 0}

    for source in sources:
        provider = source.get("provider", "").lower()
        identifier = source.get("identifier", "").strip()
        collector = COLLECTORS.get(provider)
        if not collector or not identifier:
            stats["failed_sources"] += 1
            continue
        try:
            found = collector(identifier)
            jobs.extend(found)
            stats["successful_sources"] += 1
        except Exception:
            # Discovery is best-effort. A broken external ATS must not stop other sources/users.
            stats["failed_sources"] += 1

    stats["jobs_found"] = len(jobs)
    return jobs, stats
