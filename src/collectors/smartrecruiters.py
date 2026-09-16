import re
from html import unescape

import requests
from bs4 import BeautifulSoup

from src.models import Job


BASE_URL = "https://api.smartrecruiters.com/v1/companies/{company}/postings"


def _text(value: str | None) -> str:
    if not value:
        return ""
    return BeautifulSoup(unescape(value), "html.parser").get_text(" ", strip=True)


def collect(company_identifier: str, timeout: int = 20) -> list[Job]:
    """Collect active public postings for one SmartRecruiters company."""
    url = BASE_URL.format(company=company_identifier)
    response = requests.get(url, params={"limit": 100}, timeout=timeout)
    response.raise_for_status()
    jobs: list[Job] = []

    for item in response.json().get("content", []):
        posting_id = str(item.get("id", ""))
        if not posting_id:
            continue
        detail_response = requests.get(f"{url}/{posting_id}", timeout=timeout)
        detail_response.raise_for_status()
        detail = detail_response.json()
        sections = detail.get("jobAd", {}).get("sections", {})
        description = " ".join(
            _text(section.get("text"))
            for section in sections.values()
            if isinstance(section, dict)
        )
        location = detail.get("location") or item.get("location") or {}
        location_text = ", ".join(
            str(location.get(key, "")).strip()
            for key in ("city", "region", "country")
            if location.get(key)
        )
        if location.get("remote") is True:
            location_text = f"Remote | {location_text}" if location_text else "Remote"

        company = (detail.get("company") or {}).get("name") or company_identifier
        apply_url = detail.get("applyUrl") or detail.get("ref") or item.get("ref") or ""
        jobs.append(
            Job(
                source="smartrecruiters",
                source_id=posting_id,
                title=detail.get("name") or item.get("name") or "",
                company=company,
                location=location_text,
                description=description,
                url=apply_url,
            )
        )
    return jobs
