from src.profile_extractor import extract_candidate_profile


def test_extracts_qa_profile_without_inventing_country():
    text = """
    Senior QA Analyst with 7+ years experience.
    JavaScript, Detox, BrowserStack, Postman, REST API, Android, iOS, Git and CI/CD.
    English Professional Working and Portuguese Native.
    """
    profile = extract_candidate_profile(text)
    assert profile["seniority"] == "senior"
    assert profile["years_experience"] == 7
    assert "detox" in profile["skills"]
    assert "javascript" in profile["skills"]
    assert "English" in profile["languages"]
    assert profile["country"] is None
    assert profile["remote_only"] is True


def test_accepts_explicit_country():
    profile = extract_candidate_profile("QA Engineer with Postman and API testing", country="Brazil")
    assert profile["country"] == "Brazil"


def test_profile_does_not_invent_years():
    profile = extract_candidate_profile("QA Engineer with Postman and API testing")
    assert profile["years_experience"] is None
