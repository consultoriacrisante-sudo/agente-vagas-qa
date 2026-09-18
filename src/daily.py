import os
from collections import Counter
from dataclasses import replace

from src.matcher import score_job
from src.models import Job
from src.pipeline import process_jobs
from src.storage import JobStore
from src.telegram import send_job
from src.vacancy_gate import seniority_compatible

MIN_MATCH_SCORE = int(os.environ.get("MIN_MATCH_SCORE", "60"))
MAX_JOBS_PER_USER = int(os.environ.get("MAX_JOBS_PER_USER", "8"))


def _profile_for_match(stored_profile: dict) -> dict:
    """Adapt the generic CV profile to the matcher without inventing skills."""
    skills = stored_profile.get("skills") or []
    return {
        "tracks": {
            "qa": {
                "target_titles": ["QA", "Quality Assurance", "Test", "SDET"],
                "skills": {"strong": skills, "related": []},
            },
            "salesforce": {
                "target_titles": ["Salesforce Junior", "Junior Salesforce", "Salesforce QA"],
                "skills": {
                    "learning": [s for s in skills if s.lower() in {"salesforce", "apex", "soql", "api"}]
                },
            },
        }
    }


def deliver_jobs_for_users(
    raw_jobs: list[Job],
    store: JobStore | None = None,
    only_user_id: int | None = None,
) -> dict:
    store = store or JobStore()
    eligible_jobs, rejected_jobs = process_jobs(raw_jobs, profile=None)
    rejection_reasons = Counter(job.rejection_reason or "unknown" for job in rejected_jobs)
    profiles = store.list_candidate_profiles()
    if only_user_id is not None:
        profiles = [
            row
            for row in profiles
            if int(row["telegram_user_id"]) == int(only_user_id)
        ]
    sent = 0
    ready_candidates = 0
    seniority_rejected_total = 0
    score_rejected_total = 0

    for row in profiles:
        user_id = int(row["telegram_user_id"])
        candidate = row.get("profile") or {}
        if not candidate.get("country"):
            continue
        ready_candidates += 1
        match_profile = _profile_for_match(candidate)
        ranked = []

        seniority_rejected = 0
        score_rejected = 0
        for base_job in eligible_jobs:
            compatible, _reason = seniority_compatible(base_job, candidate)
            if not compatible:
                seniority_rejected += 1
                continue
            job = score_job(replace(base_job), match_profile)
            if job.match_score >= MIN_MATCH_SCORE:
                ranked.append(job)
            else:
                score_rejected += 1

        seniority_rejected_total += seniority_rejected
        score_rejected_total += score_rejected
        ranked.sort(key=lambda j: j.match_score, reverse=True)
        delivered = 0
        for job in ranked:
            if delivered >= MAX_JOBS_PER_USER:
                break
            fingerprint = store.upsert_job(job)
            if store.already_sent(user_id, fingerprint):
                continue
            send_job(job, chat_id=user_id)
            store.mark_sent(user_id, fingerprint, job.match_score)
            delivered += 1
            sent += 1

    return {
        "candidates": len(profiles),
        "ready_candidates": ready_candidates,
        "eligible_jobs": len(eligible_jobs),
        "rejected_jobs": len(rejected_jobs),
        "rejection_reasons": dict(rejection_reasons),
        "seniority_rejected": seniority_rejected_total,
        "below_match_score": score_rejected_total,
        "sent": sent,
    }
