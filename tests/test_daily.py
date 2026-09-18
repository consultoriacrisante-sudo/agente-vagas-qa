from src.daily import deliver_jobs_for_users
from src.models import Job


class FakeStore:
    def __init__(self, country="Brazil"):
        self.sent = set()
        self.country = country

    def list_candidate_profiles(self):
        return [{
            "telegram_user_id": 123,
            "profile": {"skills": ["api", "postman", "javascript"], "country": self.country},
        }]

    def upsert_job(self, job):
        return "fingerprint-1"

    def already_sent(self, user_id, fingerprint):
        return (user_id, fingerprint) in self.sent

    def mark_sent(self, user_id, fingerprint, score):
        self.sent.add((user_id, fingerprint))


class MultiUserStore(FakeStore):
    def list_candidate_profiles(self):
        return [
            {"telegram_user_id": 123, "profile": {"skills": ["api", "postman", "javascript"], "country": "Brazil"}},
            {"telegram_user_id": 456, "profile": {"skills": ["api", "postman", "javascript"], "country": "Brazil"}},
        ]


def job():
    return Job(
        source="test",
        source_id="1",
        title="QA Engineer",
        company="Example",
        location="Brazil Remote",
        description="100% remote QA API Postman JavaScript",
        url="https://jobs.example.com/1",
        remote=True,
    )


def test_second_run_does_not_repeat(monkeypatch):
    store = FakeStore()
    monkeypatch.setattr("src.daily.send_job", lambda *args, **kwargs: None)
    first = deliver_jobs_for_users([job()], store)
    second = deliver_jobs_for_users([job()], store)
    assert first["sent"] == 1
    assert first["ready_candidates"] == 1
    assert second["sent"] == 0


def test_candidate_without_country_is_not_delivered(monkeypatch):
    store = FakeStore(country=None)
    monkeypatch.setattr("src.daily.send_job", lambda *args, **kwargs: None)
    result = deliver_jobs_for_users([job()], store)
    assert result["ready_candidates"] == 0
    assert result["sent"] == 0


def test_on_demand_delivery_targets_only_requesting_user(monkeypatch):
    store = MultiUserStore()
    recipients = []
    monkeypatch.setattr("src.daily.send_job", lambda vacancy, chat_id=None: recipients.append(chat_id))

    result = deliver_jobs_for_users([job()], store=store, only_user_id=456)

    assert result["candidates"] == 1
    assert result["ready_candidates"] == 1
    assert result["sent"] == 1
    assert recipients == [456]
    assert (456, "fingerprint-1") in store.sent
    assert (123, "fingerprint-1") not in store.sent


class SeniorStore(FakeStore):
    def list_candidate_profiles(self):
        return [{
            "telegram_user_id": 123,
            "profile": {
                "skills": ["api", "postman", "javascript"],
                "country": "Brazil",
                "seniority": "senior",
                "years_experience": 7,
            },
        }]


def test_senior_candidate_does_not_receive_junior_qa(monkeypatch):
    store = SeniorStore()
    junior = job()
    junior.title = "Analista de Testes Manuais Júnior (QA)"
    monkeypatch.setattr("src.daily.send_job", lambda *args, **kwargs: None)

    result = deliver_jobs_for_users([junior], store)

    assert result["sent"] == 0
    assert result["seniority_rejected"] == 1
