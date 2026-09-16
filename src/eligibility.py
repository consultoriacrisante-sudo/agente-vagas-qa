import re
from dataclasses import dataclass

from src.models import Job


@dataclass(slots=True)
class Eligibility:
    accepted: bool
    priority: int
    market: str
    reason: str | None = None


BRAZIL = re.compile(r"\b(brasil|brazil|br|s[aã]o paulo|rio de janeiro|belo horizonte|curitiba|porto alegre|recife)\b", re.I)
GLOBAL = re.compile(r"\b(worldwide|anywhere|global|latin america|latam|south america|americas)\b", re.I)
BLOCKED = re.compile(r"\b(us only|usa only|united states only|canada only|uk only|eu only|europe only|must reside in (?:the )?(?:us|usa|united states|canada|uk|european union))\b", re.I)


def evaluate(job: Job) -> Eligibility:
    text = " ".join([job.title, job.location, job.description])
    if BLOCKED.search(text):
        return Eligibility(False, 0, "restricted", "remote_not_eligible_from_brazil")
    if BRAZIL.search(text):
        return Eligibility(True, 100, "brazil")
    if GLOBAL.search(text):
        return Eligibility(True, 70, "international", None)
    # Remote role with no explicit country restriction can remain discoverable,
    # but below confirmed Brazil/global roles. The remote gate still applies first.
    return Eligibility(True, 40, "international_unspecified", None)
