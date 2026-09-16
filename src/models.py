from dataclasses import dataclass, field
from typing import Optional


@dataclass(slots=True)
class Job:
    source: str
    source_id: str
    title: str
    company: str
    location: str
    description: str
    url: str
    remote: Optional[bool] = None
    employment_type: str = "Não informado"
    track: Optional[str] = None
    match_score: int = 0
    matched_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    remote_evidence: list[str] = field(default_factory=list)
    rejection_reason: Optional[str] = None
