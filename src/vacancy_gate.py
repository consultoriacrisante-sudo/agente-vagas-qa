import re
from urllib.parse import urlparse

import requests

from src.models import Job


CLOSED_MARKERS = (
    "não aceita mais candidaturas",
    "nao aceita mais candidaturas",
    "não estamos mais aceitando candidaturas",
    "nao estamos mais aceitando candidaturas",
    "no longer accepting applications",
    "applications are closed",
    "applications closed",
    "application closed",
    "job is closed",
    "job has been closed",
    "position has been filled",
    "position is filled",
    "position has been closed",
    "job is no longer available",
    "job no longer available",
    "vacancy is closed",
    "vaga encerrada",
    "vaga fechada",
    "processo seletivo encerrado",
)


def _closed_text(text: str) -> bool:
    normalized = " ".join((text or "").lower().split())
    return any(marker in normalized for marker in CLOSED_MARKERS)


def vacancy_is_open(job: Job) -> tuple[bool, str | None]:
    """Reject vacancies that are explicitly closed in discovery content or live page."""
    if _closed_text(f"{job.title}\n{job.description}"):
        return False, "closed_vacancy"

    host = urlparse(job.url).netloc.lower()
    # Aggregators can keep indexed pages after applications close. Re-check them live.
    if any(name in host for name in ("linkedin.com", "indeed.", "glassdoor.", "infojobs.")):
        try:
            response = requests.get(
                job.url,
                timeout=12,
                headers={"User-Agent": "Mozilla/5.0 (compatible; AgenteVagasQA/1.0)"},
                allow_redirects=True,
            )
            if response.status_code in {404, 410}:
                return False, "closed_vacancy"
            if response.ok and _closed_text(response.text):
                return False, "closed_vacancy"
        except requests.RequestException:
            # Do not claim closure when the platform blocks validation; downstream gates remain.
            pass
    return True, None


JUNIOR_TERMS = ("junior", "júnior", "jr", "jr.", "entry level", "entry-level", "trainee", "estágio", "estagio")
SENIOR_TERMS = ("senior", "sênior", "sr", "sr.", "lead", "principal", "staff", "especialista")
MID_TERMS = ("pleno", "mid level", "mid-level", "midlevel")


def _has_term(text: str, terms: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(re.search(rf"(?<!\w){re.escape(term)}(?!\w)", lowered) for term in terms)


def seniority_compatible(job: Job, profile: dict | None) -> tuple[bool, str | None]:
    """QA respects candidate career level; Salesforce remains the intentional junior transition track."""
    if not profile or job.track != "qa":
        return True, None

    candidate = (profile.get("seniority") or "unknown").lower()
    years = profile.get("years_experience")
    title = job.title or ""

    candidate_is_senior = candidate == "senior" or isinstance(years, (int, float)) and years >= 6
    candidate_is_mid = candidate == "mid" or isinstance(years, (int, float)) and 3 <= years < 6

    if candidate_is_senior and _has_term(title, JUNIOR_TERMS):
        return False, "qa_seniority_mismatch"
    if candidate_is_mid and _has_term(title, JUNIOR_TERMS):
        return False, "qa_seniority_mismatch"
    if candidate == "junior" and _has_term(title, SENIOR_TERMS):
        return False, "qa_seniority_mismatch"
    return True, None
