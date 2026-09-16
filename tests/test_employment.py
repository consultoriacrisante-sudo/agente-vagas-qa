from src.employment import detect_employment_type


def test_detects_brazilian_types():
    assert detect_employment_type("Contratação CLT com benefícios") == "CLT"
    assert detect_employment_type("Modelo PJ, pessoa jurídica") == "PJ"


def test_contractor_is_not_pj():
    assert detect_employment_type("This role is for an independent contractor") == "Contractor"


def test_generic_contract_is_not_inferred():
    assert detect_employment_type("12 month contract role") == "Não informado"


def test_detects_explicit_employee():
    assert detect_employment_type("Full-time employee with benefits") == "Employee"


def test_conflicting_evidence_is_not_guessed():
    assert detect_employment_type("CLT or PJ depending on candidate") == "Não informado"
