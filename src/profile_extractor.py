import re

QA_SKILLS = [
    "detox", "playwright", "cypress", "appium", "robot framework", "pytest", "jest",
    "browserstack", "postman", "javascript", "python", "java", "sql", "pl/sql", "api",
    "android", "ios", "mobile", "bdd", "shift left", "ci/cd", "git", "docker", "kubernetes",
    "salesforce", "apex", "soql",
]


def _years(text: str) -> int | None:
    values = [int(v) for v in re.findall(r"(?:mais de|over|\+)?\s*(\d{1,2})\+?\s*(?:anos|years)", text, re.I)]
    return max(values) if values else None


def extract_candidate_profile(text: str, country: str | None = None) -> dict:
    clean = " ".join(text.split())
    lower = clean.lower()
    skills = sorted({skill for skill in QA_SKILLS if skill in lower})

    seniority = "unknown"
    if re.search(r"\b(senior|sênior|sr\.?|lead|líder)\b", lower):
        seniority = "senior"
    elif re.search(r"\b(junior|júnior|jr\.?|trainee|entry.level)\b", lower):
        seniority = "junior"
    elif re.search(r"\b(pleno|mid.level|mid-level)\b", lower):
        seniority = "mid"

    languages = []
    if "english" in lower or "inglês" in lower:
        languages.append("English")
    if "portuguese" in lower or "português" in lower:
        languages.append("Portuguese")

    return {
        "skills": skills,
        "years_experience": _years(clean),
        "seniority": seniority,
        "languages": languages,
        "country": country,
        "remote_only": True,
    }
