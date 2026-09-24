import json
from pathlib import Path

from src.models import Job


PROFILE_PATH = Path(__file__).resolve().parents[1] / "config" / "candidate_profile.json"


def load_profile() -> dict:
    return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))


def _skill_matches(text: str, skills: list[str]) -> list[str]:
    lowered = text.lower()
    return [skill for skill in skills if skill.lower() in lowered]


def score_job(job: Job, profile: dict | None = None) -> Job:
    profile = profile or load_profile()
    if not job.track:
        return job

    track = profile["tracks"][job.track]
    text = f"{job.title}\n{job.description}".lower()

    if job.track == "qa":
        strong = track["skills"]["strong"]
        related = track["skills"]["related"]
        matched_strong = _skill_matches(text, strong)
        matched_related = _skill_matches(text, related)
        title_hit = any(t.lower() in job.title.lower() for t in track["target_titles"])

        # Explainable relevance score, not a hiring probability. A clearly targeted
        # QA title carries meaningful weight because many ATS summaries are concise.
        skill_score = min(60, len(matched_strong) * 10 + len(matched_related) * 5)
        title_score = 25 if title_hit else 10
        remote_score = 10 if job.remote else 0

        candidate_level = str(profile.get("seniority") or "unknown").lower()
        title_lower = job.title.lower()
        senior_title = any(term in title_lower for term in ("senior", "sênior", " sr", "lead", "staff", "principal"))
        mid_title = any(term in title_lower for term in ("pleno", "mid-level", "mid level"))
        seniority_score = 0
        if candidate_level == "senior" and (senior_title or not mid_title):
            seniority_score = 10
        elif candidate_level == "mid" and (mid_title or not senior_title):
            seniority_score = 10

        job.match_score = min(100, skill_score + title_score + remote_score + seniority_score)
        job.matched_skills = matched_strong + matched_related
        job.missing_skills = [s for s in strong if s not in matched_strong][:6]
    else:
        learning = track["skills"]["learning"]
        matched = _skill_matches(text, learning)
        title_hit = any(t.lower() in job.title.lower() for t in track["target_titles"])
        # Salesforce is a transition track. Do not give a passing score merely
        # because the vacancy is remote; require candidate-relevant evidence.
        skill_score = min(55, len(matched) * 15)
        title_score = 25 if title_hit else 15
        remote_score = 10 if job.remote else 0
        job.match_score = min(100, skill_score + title_score + remote_score)
        job.matched_skills = matched
        job.missing_skills = [s for s in learning if s not in matched][:6]

    return job
