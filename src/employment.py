import re


CLT_PATTERNS = [r"\bclt\b", r"\bcarteira assinada\b"]
PJ_PATTERNS = [r"\bpj\b", r"\bpessoa jur[ií]dica\b", r"\bprestador(?:a)? de servi[cç]os\b"]
CONTRACTOR_PATTERNS = [r"\bindependent contractor\b", r"\bcontractor\b"]
EMPLOYEE_PATTERNS = [r"\bfull[- ]time employee\b", r"\bpermanent employee\b", r"\bemployment agreement\b"]


def _matches(patterns: list[str], text: str) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def detect_employment_type(text: str) -> str:
    """Return only an employment type explicitly supported by the posting.

    Generic English 'contract' is intentionally not mapped to PJ: an
    international contract can describe several legal relationships.
    """
    detected = []
    if _matches(CLT_PATTERNS, text):
        detected.append("CLT")
    if _matches(PJ_PATTERNS, text):
        detected.append("PJ")
    if _matches(CONTRACTOR_PATTERNS, text):
        detected.append("Contractor")
    if _matches(EMPLOYEE_PATTERNS, text):
        detected.append("Employee")
    return detected[0] if len(detected) == 1 else "Não informado"
