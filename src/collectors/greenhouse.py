import requests
from bs4 import BeautifulSoup

from src.models import Job


BASE_URL = "https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs"


def _text(html: str) -> str:
    return BeautifulSoup(html or "", "html.parser").get_text(" ", strip=True)


def collect(board_token: str, company: str, timeout: int = 20) -> list[Job]:
    response = requests.get(
        BASE_URL.format(board_token=board_token),
        params={"content": "true"},
        timeout=timeout,
    )
    response.raise_for_status()
    jobs: list[Job] = []
    for item in response.json().get("jobs", []):
        jobs.append(Job(
            source="greenhouse",
            source_id=str(item.get("id", "")),
            title=item.get("title", ""),
            company=company,
            location=(item.get("location") or {}).get("name", ""),
            description=_text(item.get("content", "")),
            url=item.get("absolute_url", ""),
        ))
    return jobs
