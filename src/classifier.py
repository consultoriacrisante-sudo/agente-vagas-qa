import re


QA_TERMS = (
    "qa", "quality assurance", "quality engineer", "test engineer",
    "software tester", "test automation", "sdet", "mobile qa",
)
SALESFORCE_TERMS = ("salesforce", "apex", "soql")
JUNIOR_TERMS = (
    "junior", "júnior", "jr", "entry level", "entry-level",
    "associate", "trainee", "estágio", "estagio",
)
SENIOR_TERMS = (
    "senior", "sênior", "sr", "lead", "principal", "staff", "manager",
    "architect", "especialista",
)


def _contains(text: str, terms: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(re.search(rf"(?<!\w){re.escape(term)}(?!\w)", lowered) for term in terms)


def classify_track(title: str, description: str) -> str | None:
    text = f"{title}\n{description}"
    title_lower = title.lower()

    if _contains(text, SALESFORCE_TERMS):
        # Salesforce is intentionally an entry-career track.
        if _contains(title_lower, SENIOR_TERMS):
            return None
        if _contains(text, JUNIOR_TERMS):
            return "salesforce"
        # Do not infer juniority when it is not stated.
        return None

    if _contains(text, QA_TERMS):
        return "qa"

    return None
