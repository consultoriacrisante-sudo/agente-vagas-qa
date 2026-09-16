from src.classifier import classify_track


def test_classifies_qa():
    assert classify_track("QA Automation Engineer", "Playwright API testing") == "qa"


def test_accepts_junior_salesforce():
    assert classify_track("Junior Salesforce Developer", "Apex and Salesforce") == "salesforce"


def test_rejects_senior_salesforce():
    assert classify_track("Senior Salesforce Developer", "Salesforce Apex") is None


def test_does_not_infer_salesforce_juniority():
    assert classify_track("Salesforce Developer", "Apex") is None
