import requests
from bs4 import BeautifulSoup

from src.models import Job


BASE_URL = "https://api.lever.co/v0/postings/{site}"


def _text(value: str) -> str:
    return BeautifulSoup(value or "", "html.parser").get_text(" ", strip=True)


def collect(site: str, company: str, timeout: int = 20) -> list[Job]:
    response = requests.get(
        BASE_URL.format(site=site),
        params={"mode": "json"},
        timeout=timeout,
    )
    response.raise_for_status()
    jobs: list[Job] = []
    for item in response.json():
        categories = item.get("categories") or {}
        description_parts = [
            item.get("descriptionPlain") or _text(item.get("description", "")),
            _text(item.get("additional", "")),
        ]
        for section in item.get("lists") or []:
            description_parts.append(section.get("text", ""))
            description_parts.append(_text(section.get("content", "")))
        jobs.append(Job(
            source="lever",
            source_id=item.get("id", ""),
            title=item.get("text", ""),
            company=company,
            location=categories.get("location", ""),
            description="\n".join(filter(None, description_parts)),
            url=item.get("hostedUrl") or item.get("applyUrl", ""),
        ))
    return jobs
