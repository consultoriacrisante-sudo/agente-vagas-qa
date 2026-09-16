from collections.abc import Iterable

from src.classifier import classify_track
from src.dedupe import job_fingerprint
from src.eligibility import evaluate
from src.employment import detect_employment_type
from src.matcher import score_job
from src.models import Job
from src.remote_gate import validate_remote
from src.url_gate import valid_application_url


def process_jobs(jobs: Iterable[Job], profile: dict | None = None) -> tuple[list[Job], list[Job]]:
    accepted: list[tuple[int, Job]] = []
    rejected: list[Job] = []
    seen: set[str] = set()

    for job in jobs:
        if not valid_application_url(job.url):
            job.rejection_reason = "invalid_application_url"
            rejected.append(job)
            continue

        remote = validate_remote(job.title, job.location, job.description)
        job.remote = remote.accepted
        job.remote_evidence = remote.evidence
        if not remote.accepted:
            job.rejection_reason = remote.reason
            rejected.append(job)
            continue

        eligibility = evaluate(job)
        if not eligibility.accepted:
            job.rejection_reason = eligibility.reason
            rejected.append(job)
            continue

        job.track = classify_track(job.title, job.description)
        if not job.track:
            job.rejection_reason = "outside_target_tracks"
            rejected.append(job)
            continue

        job.employment_type = detect_employment_type(job.description)
        score_job(job, profile)

        fingerprint = job_fingerprint(
            job.source_id, job.company, job.title, job.location, job.url
        )
        if fingerprint in seen:
            job.rejection_reason = "duplicate_in_run"
            rejected.append(job)
            continue
        seen.add(fingerprint)
        accepted.append((eligibility.priority, job))

    accepted.sort(key=lambda item: (item[0], item[1].match_score), reverse=True)
    return [job for _, job in accepted], rejected
