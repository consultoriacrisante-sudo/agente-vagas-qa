from src.models import Job
from src.vacancy_gate import seniority_compatible, vacancy_is_open


def make_job(title="QA Engineer", description="100% remote QA role"):
    return Job(
        source="linkedin",
        source_id="1",
        title=title,
        company="Example",
        location="Brazil Remote",
        description=description,
        url="https://www.linkedin.com/jobs/view/123456/",
        remote=True,
        track="qa",
    )


def test_rejects_closed_vacancy_from_discovery_content():
    job = make_job(description="100% remote. Não aceita mais candidaturas.")
    accepted, reason = vacancy_is_open(job)
    assert accepted is False
    assert reason == "closed_vacancy"


def test_senior_qa_candidate_rejects_junior_qa_title():
    job = make_job(title="Analista de Testes Manuais Júnior (QA)")
    accepted, reason = seniority_compatible(
        job, {"seniority": "senior", "years_experience": 7}
    )
    assert accepted is False
    assert reason == "qa_seniority_mismatch"


def test_senior_qa_candidate_accepts_senior_qa_title():
    job = make_job(title="Senior QA Engineer")
    accepted, reason = seniority_compatible(
        job, {"seniority": "senior", "years_experience": 7}
    )
    assert accepted is True
    assert reason is None


def test_salesforce_transition_is_not_blocked_by_qa_seniority():
    job = make_job(title="Salesforce Junior QA")
    job.track = "salesforce"
    accepted, reason = seniority_compatible(
        job, {"seniority": "senior", "years_experience": 7}
    )
    assert accepted is True
    assert reason is None
