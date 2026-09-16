import re


CLT_PATTERNS = [r"\bclt\b", r"\bcarteira assinada\b"]
PJ_PATTERNS = [r"\bpj\b", r"\bpessoa jur[ií]dica\b", r"\bcontractor\b", r"\bcontract\b"]


def detect_employment_type(text: str) -> str:
    has_clt = any(re.search(p, text, re.IGNORECASE) for p in CLT_PATTERNS)
    has_pj = any(re.search(p, text, re.IGNORECASE) for p in PJ_PATTERNS)
    if has_clt and not has_pj:
        return "CLT"
    if has_pj and not has_clt:
        return "PJ"
    return "Não informado"
