import hashlib
import os
from urllib.parse import urlparse

import requests

from src.models import Job

TAVILY_URL = "https://api.tavily.com/search"
SEARCH_QUERIES = [
    'QA remote Brazil vaga "100% remoto"',
    'Quality Assurance remote Brazil jobs',
    'QA Engineer remote LATAM Brazil',
    'Salesforce junior remote Brazil vaga',
    'Junior Salesforce remote LATAM Brazil',
]
ALLOWED_JOB_HOST_HINTS = (
    "linkedin.com", "indeed.com", "glassdoor.com", "infojobs.com",
    "greenhouse.io", "lever.co", "ashbyhq.com", "smartrecruiters.com",
    "jobs.", "careers.", "workdayjobs.com",
)


def _looks_like_job_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False
    host = parsed.netloc.lower()
    return any(hint in host for hint in ALLOWED_JOB_HOST_HINTS)


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
