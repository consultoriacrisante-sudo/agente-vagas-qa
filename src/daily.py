import os
from dataclasses import replace

from src.matcher import score_job
from src.models import Job
from src.pipeline import process_jobs
from src.storage import JobStore
from src.telegram import send_job

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
    # URL/remote/geo/track gates that do not depend on the candidate.
    eligible_jobs, rejected_jobs = process_jobs(raw_jobs, profile=None)
    profiles = store.list_candidate_profiles()
    if only_user_id is not None:
        profiles = [
            row
            for row in profiles
            if int(row["telegram_user_id"]) == int(only_user_id)
        ]
    sent = 0
    ready_candidates = 0

    for row in profiles:
        user_id = int(row["telegram_user_id"])
        candidate = row.get("profile") or {}
        if not candidate.get("country"):
            continue
        ready_candidates += 1
        match_profile = _profile_for_match(candidate)
        ranked = []

        # Re-run candidate-dependent gates with the actual CV profile.
        # This is what prevents a senior QA candidate from receiving Junior QA,
        # while keeping Salesforce Junior available as an intentional transition track.
        candidate_jobs, _candidate_rejected = process_jobs(
            [replace(job) for job in eligible_jobs],
            profile=candidate,
        )

        for base_job in candidate_jobs:
            job = score_job(replace(base_job), match_profile)
            if job.match_score >= MIN_MATCH_SCORE:
                ranked.append(job)

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
        "sent": sent,
    }
