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

        # Explainable relevance score, not a hiring probability.
        skill_score = min(70, len(matched_strong) * 7 + len(matched_related) * 4)
        title_score = 20 if title_hit else 10
        remote_score = 10 if job.remote else 0
        job.match_score = min(100, skill_score + title_score + remote_score)
        job.matched_skills = matched_strong + matched_related
        job.missing_skills = [s for s in strong if s not in matched_strong][:6]
    else:
        learning = track["skills"]["learning"]
        matched = _skill_matches(text, learning)
        # Salesforce is a transition track: score opportunity relevance, not senior QA fit.
        job.match_score = min(100, 55 + len(matched) * 7 + (10 if job.remote else 0))
        job.matched_skills = matched
        job.missing_skills = [s for s in learning if s not in matched][:6]

    return job
