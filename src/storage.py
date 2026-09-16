import os
from datetime import datetime, timezone

from supabase import Client, create_client

from src.dedupe import job_fingerprint
from src.models import Job


class JobStore:
    def __init__(self, client: Client | None = None):
        self.client = client or create_client(
            os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"]
        )

    def upsert_candidate_profile(
        self,
        telegram_user_id: int,
        profile: dict,
        display_name: str = "",
        resume_file_name: str = "",
        resume_mime_type: str = "",
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        payload = {
            "telegram_user_id": telegram_user_id,
            "display_name": display_name,
            "resume_file_name": resume_file_name,
            "resume_mime_type": resume_mime_type,
            "profile": profile,
            "updated_at": now,
        }
        self.client.table("candidate_profiles").upsert(
            payload, on_conflict="telegram_user_id"
        ).execute()

    def list_candidate_profiles(self) -> list[dict]:
        result = self.client.table("candidate_profiles").select("*").execute()
        return list(result.data or [])

    def upsert_job(self, job: Job) -> str:
        fingerprint = job_fingerprint(
            job.source_id, job.company, job.title, job.location, job.url, source=job.source
        )
        payload = {
            "fingerprint": fingerprint,
            "source": job.source,
            "source_job_id": job.source_id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "description": job.description,
            "canonical_url": job.url,
            "employment_type": job.employment_type,
            "track": job.track,
            "discovered_at": datetime.now(timezone.utc).isoformat(),
        }
        self.client.table("jobs").upsert(payload, on_conflict="fingerprint").execute()
        return fingerprint

    def already_sent(self, telegram_user_id: int, fingerprint: str) -> bool:
        result = (
            self.client.table("job_deliveries")
            .select("id")
            .eq("telegram_user_id", telegram_user_id)
            .eq("job_fingerprint", fingerprint)
            .limit(1)
            .execute()
        )
        return bool(result.data)

    def mark_sent(self, telegram_user_id: int, fingerprint: str, score: int) -> None:
        self.client.table("job_deliveries").insert(
            {
                "telegram_user_id": telegram_user_id,
                "job_fingerprint": fingerprint,
                "match_score": score,
                "sent_at": datetime.now(timezone.utc).isoformat(),
            }
        ).execute()
