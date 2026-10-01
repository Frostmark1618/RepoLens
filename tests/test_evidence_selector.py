from llm.evidence_selector import (
    select_claim_evidence,
)


def test_architecture_query_prefers_architecture():
    evidence = [
        {
            "evidence_type": "code",
            "file": "src/requests/sessions.py",
            "start_line": 901,
            "end_line": 920,
        },
        {
            "evidence_type": "architecture",
            "module_name": "requests.sessions",
        },
    ]

    selected = select_claim_evidence(
        "session dependencies",
        evidence,
    )

    assert len(selected) == 1
    assert (
        selected[0]["evidence_type"]
        == "architecture"
    )

    print(
        "Architecture selection passed."
    )


def test_symbol_query_prefers_code():
    evidence = [
        {
            "evidence_type": "code",
            "file": "docs/example.py",
            "start_line": 1,
            "end_line": 20,
        },
        {
            "evidence_type": "architecture",
            "module_name": "requests.sessions",
        },
    ]

    selected = select_claim_evidence(
        "FlaskyStyle class",
        evidence,
    )

    assert len(selected) == 1
    assert (
        selected[0]["evidence_type"]
        == "code"
    )

    print(
        "Code selection passed."
    )


def test_concept_query_keeps_all_evidence():
    evidence = [
        {
            "evidence_type": "code",
            "file": "src/requests/sessions.py",
            "start_line": 1,
            "end_line": 20,
        },
        {
            "evidence_type": "architecture",
            "module_name": "requests.sessions",
        },
    ]

    selected = select_claim_evidence(
        "HTTP request handling",
        evidence,
    )

    assert len(selected) == 2

    print(
        "General evidence selection passed."
    )


def test_architecture_claim_evidence_prefers_exact_module():
    evidence = [
        {
            "evidence_type": "architecture",
            "module_name": "requests.models",
        },
        {
            "evidence_type": "architecture",
            "module_name": "requests.sessions",
        },
        {
            "evidence_type": "architecture",
            "module_name": "requests.utils",
        },
    ]

    selected = select_claim_evidence(
        "What does requests.sessions depend on?",
        evidence,
    )

    assert len(selected) == 1
    assert selected[0]["module_name"] == "requests.sessions"

if __name__ == "__main__":
    test_architecture_query_prefers_architecture()
    test_symbol_query_prefers_code()
    test_concept_query_keeps_all_evidence()
    test_architecture_claim_evidence_prefers_exact_module()
    print(
        "Evidence selector tests passed."
    )