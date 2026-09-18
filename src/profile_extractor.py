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

    years_experience = _years(clean)

    # Prefer explicit senior-level evidence and years over incidental junior words
    # elsewhere in a CV (for example, an old role or course title).
    seniority = "unknown"
    if re.search(r"\b(senior|sênior|sr\.?|lead|líder)\b", lower) or (
        years_experience is not None and years_experience >= 6
    ):
        seniority = "senior"
    elif re.search(r"\b(pleno|mid.level|mid-level)\b", lower) or (
        years_experience is not None and years_experience >= 3
    ):
        seniority = "mid"
    elif re.search(r"\b(junior|júnior|jr\.?|trainee|entry.level)\b", lower):
        seniority = "junior"

    languages = []
    if "english" in lower or "inglês" in lower:
        languages.append("English")
    if "portuguese" in lower or "português" in lower:
        languages.append("Portuguese")

    return {
        "skills": skills,
        "years_experience": years_experience,
        "seniority": seniority,
        "languages": languages,
        "country": country,
        "remote_only": True,
    }
