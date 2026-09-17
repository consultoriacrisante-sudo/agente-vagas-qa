import hashlib
import os
from urllib.parse import parse_qs, urlparse

import requests

from src.models import Job

TAVILY_URL = "https://api.tavily.com/search"
SEARCH_QUERIES = [
    'QA remote Brazil vaga "100% remoto"',
    'Quality Assurance remote Brazil jobs',
    'QA Engineer remote LATAM Brazil',
    'Salesforce junior remote Brazil vaga',
    'Junior Salesforce remote LATAM Brazil',
    'QA remote Brazil site:boards.greenhouse.io OR site:jobs.lever.co',
    'QA remote LATAM site:jobs.ashbyhq.com OR site:jobs.smartrecruiters.com',
]


def _path_parts(parsed) -> list[str]:
    return [part for part in parsed.path.split("/") if part]


def _looks_like_job_url(url: str) -> bool:
    """Accept individual vacancy/application pages, never generic search/listing pages."""
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False

    host = parsed.netloc.lower().removeprefix("www.")
    path = parsed.path.lower()
    parts = _path_parts(parsed)
    query = parse_qs(parsed.query)

    if "linkedin.com" in host:
        return "/jobs/view/" in path and len(parts) >= 3
    if "indeed." in host:
        return path.rstrip("/").endswith("/viewjob") and bool(query.get("jk"))
    if "glassdoor." in host:
        return "/job-listing/" in path or bool(query.get("jl"))
    if "infojobs." in host:
        return len(parts) >= 2 and any(term in path for term in ("vaga", "vagas", "job", "oferta"))
    if "greenhouse.io" in host:
        return len(parts) >= 2 and ("/jobs/" in path or "/job_app" in path)
    if "lever.co" in host:
        return len(parts) >= 2
    if "ashbyhq.com" in host:
        return len(parts) >= 2
    if "smartrecruiters.com" in host:
        return len(parts) >= 3 and any(term in path for term in ("job", "jobs"))
    if "workdayjobs.com" in host or "myworkdayjobs.com" in host:
        return len(parts) >= 2 and "/job/" in path

    if host.startswith("jobs.") or host.startswith("careers."):
        return len(parts) >= 2 and any(
            term in path for term in ("/job/", "/jobs/", "position", "vacancy", "opening", "requisition")
        )
    return False


def _source(url: str) -> str:
    host = urlparse(url).netloc.lower().removeprefix("www.")
    for name in ("linkedin", "indeed", "glassdoor", "infojobs", "greenhouse", "lever", "ashby", "smartrecruiters", "workday"):
        if name in host:
            return name
    return host or "web"


def search_jobs(queries: list[str] | None = None) -> list[Job]:
    """Discover candidate vacancy pages. Hard gates later validate remote/eligibility/track."""
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        return []

    jobs: list[Job] = []
    seen: set[str] = set()
    for query in queries or SEARCH_QUERIES:
        try:
            response = requests.post(
                TAVILY_URL,
                json={
                    "api_key": api_key,
                    "query": query,
                    "search_depth": "advanced",
                    "max_results": 10,
                    "include_raw_content": True,
                },
                timeout=30,
            )
            response.raise_for_status()
        except requests.RequestException:
            continue

        for result in response.json().get("results", []):
            url = (result.get("url") or "").strip()
            if not _looks_like_job_url(url) or url in seen:
                continue
            seen.add(url)
            title = (result.get("title") or "").strip()
            description = (result.get("raw_content") or result.get("content") or "").strip()
            if not title or not description:
                continue
            source = _source(url)
            source_id = hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]
            jobs.append(Job(
                source=source,
                source_id=source_id,
                title=title,
                company="Não informado",
                location="Não informado",
                description=description,
                url=url,
            ))
    return jobs
