import re
from dataclasses import dataclass


REMOTE_PATTERNS = [
    r"\b100%\s*(?:remote|remoto|remota)\b",
    r"\bfully\s+remote\b",
    r"\bremote[- ]first\b",
    r"\btrabalho\s+remoto\b",
    r"\bwork\s+from\s+home\b",
    r"\bhome\s+office\b",
    r"\bremote\b",
    r"\bremot[oa]\b",
]

CONTRADICTION_PATTERNS = [
    r"\bhybrid\b",
    r"\bh[ií]brid[oa]\b",
    r"\bon[- ]site\b",
    r"\bonsite\b",
    r"\bpresencial\b",
    r"\bin[- ]office\b",
    r"\b(?:1|2|3|4|5)\s+days?\s+(?:a|per)\s+week\s+(?:in|at)\s+(?:the\s+)?office\b",
    r"\b(?:1|2|3|4|5)x\s+(?:por|na)\s+semana\s+(?:no\s+)?escrit[oó]rio\b",
    r"\bmust\s+(?:work|be)\s+(?:from|in|at)\s+(?:the\s+)?office\b",
]


@dataclass(frozen=True, slots=True)
class RemoteDecision:
    accepted: bool
    evidence: list[str]
    reason: str


def _matches(patterns: list[str], text: str) -> list[str]:
    found: list[str] = []
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            found.append(match.group(0))
    return found


def validate_remote(title: str, location: str, description: str) -> RemoteDecision:
    text = "\n".join(filter(None, [title, location, description]))
    contradictions = _matches(CONTRADICTION_PATTERNS, text)
    if contradictions:
        return RemoteDecision(False, contradictions, "hybrid_or_onsite_evidence")

    remote_evidence = _matches(REMOTE_PATTERNS, text)
    if not remote_evidence:
        return RemoteDecision(False, [], "remote_not_confirmed")

    return RemoteDecision(True, remote_evidence, "remote_confirmed")
