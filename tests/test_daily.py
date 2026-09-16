from src.daily import deliver_jobs_for_users
from src.models import Job


class FakeStore:
    def __init__(self):
        self.sent = set()

    def list_candidate_profiles(self):
        return [{"telegram_user_id": 123, "profile": {"skills": ["api", "postman", "javascript"]}}]

    def upsert_job(self, job):
        return "fingerprint-1"

    def already_sent(self, user_id, fingerprint):
        return (user_id, fingerprint) in self.sent

    def mark_sent(self, user_id, fingerprint, score):
        self.sent.add((user_id, fingerprint))


def job():
    return Job(source="test", source_id="1", title="QA Engineer", company="Example", location="Brazil Remote", description="100% remote QA API Postman JavaScript", url="https://jobs.example.com/1", remote=True)


def test_second_run_does_not_repeat(monkeypatch):
    store = FakeStore()
    monkeypatch.setattr("src.daily.send_job", lambda *args, **kwargs: None)
    first = deliver_jobs_for_users([job()], store)
    second = deliver_jobs_for_users([job()], store)
    assert first["sent"] == 1
    assert second["sent"] == 0
