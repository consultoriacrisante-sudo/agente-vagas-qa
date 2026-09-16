import requests
from bs4 import BeautifulSoup

from src.models import Job


BASE_URL = "https://api.ashbyhq.com/posting-api/job-board/{board}"


def _text(value: str) -> str:
    return BeautifulSoup(value or "", "html.parser").get_text(" ", strip=True)


def collect(board: str, company: str, timeout: int = 20) -> list[Job]:
    response = requests.get(
        BASE_URL.format(board=board),
        params={"includeCompensation": "true"},
        timeout=timeout,
    )
    response.raise_for_status()
    jobs: list[Job] = []
    for item in response.json().get("jobs", []):
        description = item.get("descriptionPlain") or _text(item.get("descriptionHtml", ""))
        location = item.get("location", "")
        secondary = [x.get("location", "") for x in item.get("secondaryLocations", [])]
        location = ", ".join(filter(None, [location, *secondary]))
        jobs.append(Job(
            source="ashby",
            source_id=item.get("id", "") or item.get("jobUrl", ""),
            title=item.get("title", ""),
            company=company,
            location=location,
            description=description,
            url=item.get("jobUrl") or item.get("applyUrl", ""),
        ))
    return jobs
