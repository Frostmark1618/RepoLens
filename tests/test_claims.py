from llm.answer import build_answer
from llm.claims import AnswerClaim


def test_claim_contract():
    claim = AnswerClaim(
        "requests.sessions has 12 outgoing dependencies.",
        "FACT",
        [
            {
                "evidence_type": "architecture",
                "module_name": "requests.sessions",
            }
        ],
    )

    assert claim.status == "fact"
    assert (
        claim.text
        == "requests.sessions has 12 outgoing dependencies."
    )
    assert len(claim.evidence) == 1

    print("Normalized status:", claim.status)
    print("Claim evidence:", claim.evidence)

    try:
        AnswerClaim(
            "test",
            "unsupported",
        )
    except ValueError as error:
        print("Validation error:", error)
    else:
        raise AssertionError(
            "Unsupported claim status was accepted."
        )


def test_answer_backward_compatibility():
    result = build_answer(
        "FACT: requests.sessions has dependencies.",
        "fact",
        [
            {
                "evidence_type": "architecture",
                "module_name": "requests.sessions",
            }
        ],
    )

    assert (
        result["answer"]
        == "FACT: requests.sessions has dependencies."
    )
    assert result["status"] == "fact"
    assert len(result["evidence"]) == 1
    assert result["claims"] == []

    print("Backward compatibility test passed.")


def test_answer_with_claims():
    claim = AnswerClaim(
        "requests.sessions has 12 outgoing dependencies.",
        "fact",
        [
            {
                "evidence_type": "architecture",
                "module_name": "requests.sessions",
            }
        ],
    )

    result = build_answer(
        "requests.sessions has 12 outgoing dependencies.",
        "fact",
        claim.evidence,
        [claim],
    )

    assert len(result["claims"]) == 1
    assert result["claims"][0] is claim
    assert result["claims"][0].status == "fact"

    print("Claim-integrated answer test passed.")


def test_answer_service_validates_evidence():
    from llm.answer_service import (
        generate_repository_answer,
    )
    from llm.fake_provider import (
        FakeLLMProvider,
    )

    valid_evidence = [
        {
            "evidence_type": "architecture",
            "module_name": "requests.sessions",
        }
    ]

    result = generate_repository_answer(
        query="session dependencies",
        repository_context="requests.sessions has 12 outgoing dependencies.",
        provider=FakeLLMProvider(
            "FACT: requests.sessions has 12 outgoing dependencies."
        ),
        evidence=valid_evidence,
    )

    assert result["evidence"] == valid_evidence

    invalid_evidence = [
        {
            "evidence_type": "invalid",
        }
    ]

    try:
        generate_repository_answer(
            query="session dependencies",
            repository_context="requests.sessions has dependencies.",
            provider=FakeLLMProvider(
                "FACT: test"
            ),
            evidence=invalid_evidence,
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Invalid evidence was accepted."
        )

    print(
        "Answer service evidence validation passed."
    )

def test_multi_claim_decomposition_contract():
    from llm.claim_decomposer import (
        decompose_answer_into_claims,
    )

    answer = (
        "FACT: requests.sessions has 12 outgoing "
        "dependencies and 1 incoming dependency."
    )

    claims = decompose_answer_into_claims(answer)

    assert len(claims) == 2

    assert (
        claims[0]
        == "requests.sessions has 12 outgoing dependencies."
    )

    assert (
        claims[1]
        == "requests.sessions has 1 incoming dependency."
    )

    print(
        "Multi-claim decomposition contract passed."
    )

def test_multi_claims_have_independent_evidence():
    from llm.claims import AnswerClaim

    claims = [
        AnswerClaim(
            "requests.sessions has 12 outgoing dependencies.",
            "fact",
            [
                {
                    "evidence_type": "architecture",
                    "module_name": "requests.sessions",
                }
            ],
        ),
        AnswerClaim(
            "requests.sessions has 1 incoming dependency.",
            "fact",
            [
                {
                    "evidence_type": "architecture",
                    "module_name": "requests.sessions",
                }
            ],
        ),
    ]

    assert len(claims) == 2
    assert claims[0].evidence is not claims[1].evidence
    assert claims[0].evidence[0]["module_name"] == (
        "requests.sessions"
    )
    assert claims[1].evidence[0]["module_name"] == (
        "requests.sessions"
    )

    print(
        "Independent claim evidence contract passed."
    )
def test_repository_qa_builds_multiple_claims():
    from llm.fake_provider import FakeLLMProvider
    from llm.repository_qa import answer_repository_query

    chunks = [
        {
            "file": "src/requests/sessions.py",
            "start_line": 501,
            "end_line": 550,
            "content": (
                "def prepare_request(self, request):\n"
                "    pass\n"
            ),
        }
    ]

    architecture_snapshot = {
        "production_modules": [
            {
                "module_name": "requests.sessions",
                "file": "src/requests/sessions.py",
                "layer": "source",
                "outgoing_dependencies": [
                    "requests.models",
                    "requests.adapters",
                ],
                "incoming_dependencies": [
                    "requests.api",
                ],
            }
        ],
        "graph_summary": {
            "node_count": 1,
            "edge_count": 1,
            "isolated_node_count": 0,
            "isolated_nodes": [],
            "top_connected_nodes": [],
        },
    }

    provider = FakeLLMProvider(
        "FACT: requests.sessions has 2 outgoing "
        "dependencies and 1 incoming dependency."
    )

    result = answer_repository_query(
        query="What does requests.sessions depend on?",
        chunks=chunks,
        provider=provider,
        architecture_snapshot=architecture_snapshot,
    )

    claims = result["claims"]

    coverage = result["claim_coverage"]

    assert coverage["claim_count"] == 2
    assert coverage["supported_claims"] == 2
    assert coverage["unsupported_claims"] == 0
    assert coverage["coverage"] == 1.0

    assert len(claims) == 2

    assert (
        claims[0].text
        == "requests.sessions has 2 outgoing dependencies."
    )

    assert (
        claims[1].text
        == "requests.sessions has 1 incoming dependency."
    )

    assert claims[0].status == "fact"
    assert claims[1].status == "fact"

    assert len(claims[0].evidence) >= 1
    assert len(claims[1].evidence) >= 1

    assert (
        claims[0].evidence[0]["evidence_type"]
        == "architecture"
    )

    assert (
        claims[1].evidence[0]["evidence_type"]
        == "architecture"
    )

    assert (
        claims[0].evidence[0]["module_name"]
        == "requests.sessions"
    )

    assert (
        claims[1].evidence[0]["module_name"]
        == "requests.sessions"
    )

    print(
        "Repository QA multi-claim integration passed."
    )


def test_unknown_claim_has_no_evidence():
    from llm.fake_provider import FakeLLMProvider
    from llm.repository_qa import answer_repository_query

    chunks = [
        {
            "file": "src/requests/sessions.py",
            "start_line": 901,
            "end_line": 920,
            "content": (
                "def send(self, request, **kwargs):\n"
                "    return self.adapters.get(request.url)\n"
            ),
        }
    ]

    architecture_snapshot = {
        "production_modules": [
            {
                "module_name": "requests.sessions",
                "file": "src/requests/sessions.py",
                "layer": "source",
                "outgoing_dependencies": [
                    "requests.models",
                    "requests.adapters",
                ],
                "incoming_dependencies": [
                    "requests.api",
                ],
            }
        ],
        "graph_summary": {
            "node_count": 1,
            "edge_count": 1,
            "isolated_node_count": 0,
            "isolated_nodes": [],
            "top_connected_nodes": [],
        },
    }

    provider = FakeLLMProvider(
        "UNKNOWN: The repository evidence does not "
        "establish which database requests.sessions uses."
    )

    result = answer_repository_query(
        query="Which database does requests.sessions use?",
        chunks=chunks,
        provider=provider,
        architecture_snapshot=architecture_snapshot,
    )

    assert result["status"] == "unknown"

    assert len(result["claims"]) == 1

    claim = result["claims"][0]
    coverage = result["claim_coverage"]

    assert coverage["claim_count"] == 1
    assert coverage["supported_claims"] == 0
    assert coverage["unsupported_claims"] == 1
    assert coverage["coverage"] == 0.0

    assert claim.status == "unknown"

    assert (
        claim.text
        == "The repository evidence does not establish "
        "which database requests.sessions uses."
    )

    assert claim.evidence == []

    print(
        "Unknown claim evidence isolation passed."
    )

def test_claim_evidence_prefers_claim_relevant_architecture():
    from llm.evidence_selector import select_claim_evidence

    evidence = [
        {
            "evidence_type": "architecture",
            "module_name": "requests.models",
            "file": "src/requests/models.py",
        },
        {
            "evidence_type": "architecture",
            "module_name": "requests.sessions",
            "file": "src/requests/sessions.py",
        },
        {
            "evidence_type": "architecture",
            "module_name": "requests.adapters",
            "file": "src/requests/adapters.py",
        },
    ]

    selected = select_claim_evidence(
        query="requests.sessions has 12 outgoing dependencies.",
        evidence=evidence,
    )

    assert len(selected) == 1

    assert (
        selected[0]["module_name"]
        == "requests.sessions"
    )

    print(
        "Claim-relevant architecture evidence passed."
    )

def test_claim_evidence_coverage():
    from llm.claim_coverage import (
        calculate_claim_coverage,
    )
    from llm.claims import AnswerClaim

    claims = [
        AnswerClaim(
            "requests.sessions has 12 outgoing dependencies.",
            "fact",
            [
                {
                    "evidence_type": "architecture",
                    "module_name": "requests.sessions",
                }
            ],
        ),
        AnswerClaim(
            "requests.sessions has 1 incoming dependency.",
            "fact",
            [
                {
                    "evidence_type": "architecture",
                    "module_name": "requests.sessions",
                }
            ],
        ),
        AnswerClaim(
            "The repository does not establish which database is used.",
            "unknown",
            [],
        ),
    ]

    coverage = calculate_claim_coverage(
        claims
    )

    assert coverage["claim_count"] == 3
    assert coverage["supported_claims"] == 2
    assert coverage["unsupported_claims"] == 1
    assert coverage["coverage"] == 0.6667

    print(
        "Claim evidence coverage passed."
    )

def test_risk_signal_builds_evidence_backed_claim():
    from llm.risk_claims import (
        build_risk_claim,
    )

    risk_signal = {
        "file": "src/requests/sessions.py",
        "module_name": "requests.sessions",
        "signal": "high_connectivity",
        "connection_count": 13,
        "incoming_count": 1,
        "outgoing_count": 12,
        "severity": "medium",
        "status": "possible_risk",
        "reason": (
            "This module has 13 dependency connections "
            "(1 incoming and 12 outgoing)."
        ),
        "evidence": {
            "file": "src/requests/sessions.py",
            "incoming_dependencies": [
                "requests.api",
            ],
            "outgoing_dependencies": [
                "requests.models",
                "requests.adapters",
            ],
            "incoming_count": 1,
            "outgoing_count": 12,
            "total_connections": 13,
        },
    }

    claim = build_risk_claim(
        risk_signal
    )

    assert claim.status == "possible_risk"

    assert (
    "requests.sessions has "
    "13 dependency connections."
    in claim.text
)

    

    assert len(claim.evidence) == 1

    assert (
        claim.evidence[0]["evidence_type"]
        == "architecture"
    )

    assert (
        claim.evidence[0]["module_name"]
        == "requests.sessions"
    )

    print(
        "Risk claim evidence contract passed."
    )

def test_risk_claims_have_full_evidence_coverage():
    from llm.claim_coverage import (
        calculate_claim_coverage,
    )
    from llm.risk_claims import (
        build_risk_claim,
    )

    risk_signals = [
        {
            "file": "src/requests/models.py",
            "module_name": "requests.models",
            "signal": "high_connectivity",
            "connection_count": 20,
            "incoming_count": 10,
            "outgoing_count": 10,
            "severity": "high",
            "status": "possible_risk",
            "reason": (
                "This module has 20 dependency connections."
            ),
            "evidence": {
                "file": "src/requests/models.py",
                "incoming_dependencies": [],
                "outgoing_dependencies": [],
                "incoming_count": 10,
                "outgoing_count": 10,
                "total_connections": 20,
            },
        },
        {
            "file": "src/requests/sessions.py",
            "module_name": "requests.sessions",
            "signal": "high_connectivity",
            "connection_count": 13,
            "incoming_count": 1,
            "outgoing_count": 12,
            "severity": "medium",
            "status": "possible_risk",
            "reason": (
                "This module has 13 dependency connections."
            ),
            "evidence": {
                "file": "src/requests/sessions.py",
                "incoming_dependencies": [],
                "outgoing_dependencies": [],
                "incoming_count": 1,
                "outgoing_count": 12,
                "total_connections": 13,
            },
        },
    ]

    claims = [
        build_risk_claim(signal)
        for signal in risk_signals
    ]

    coverage = calculate_claim_coverage(
        claims
    )

    assert coverage["claim_count"] == 2
    assert coverage["supported_claims"] == 2
    assert coverage["unsupported_claims"] == 0
    assert coverage["coverage"] == 1.0

    for claim in claims:
        assert claim.status == "possible_risk"
        assert len(claim.evidence) == 1
        assert (
            claim.evidence[0]["evidence_type"]
            == "architecture"
        )

    print(
        "Risk claim coverage passed."
    )

def test_unified_risk_report_contract():
    from llm.risk_report import (
        build_risk_report,
    )

    risk_signals = [
        {
            "file": "src/requests/models.py",
            "module_name": "requests.models",
            "signal": "high_connectivity",
            "connection_count": 20,
            "incoming_count": 10,
            "outgoing_count": 10,
            "severity": "high",
            "status": "possible_risk",
            "reason": (
                "This module has 20 dependency connections."
            ),
            "evidence": {
                "file": "src/requests/models.py",
                "incoming_dependencies": [],
                "outgoing_dependencies": [],
                "incoming_count": 10,
                "outgoing_count": 10,
                "total_connections": 20,
            },
        },
        {
            "file": "src/requests/sessions.py",
            "module_name": "requests.sessions",
            "signal": "high_connectivity",
            "connection_count": 13,
            "incoming_count": 1,
            "outgoing_count": 12,
            "severity": "medium",
            "status": "possible_risk",
            "reason": (
                "This module has 13 dependency connections."
            ),
            "evidence": {
                "file": "src/requests/sessions.py",
                "incoming_dependencies": [],
                "outgoing_dependencies": [],
                "incoming_count": 1,
                "outgoing_count": 12,
                "total_connections": 13,
            },
        },
    ]

    report = build_risk_report(
        risk_signals
    )

    assert report["risk_signal_count"] == 2
    assert report["claim_count"] == 2

    assert (
        report["coverage"]["claim_count"]
        == 2
    )

    assert (
        report["coverage"]["supported_claims"]
        == 2
    )

    assert (
        report["coverage"]["unsupported_claims"]
        == 0
    )

    assert (
        report["coverage"]["coverage"]
        == 1.0
    )

    assert len(report["claims"]) == 2

    assert (
        report["claims"][0].status
        == "possible_risk"
    )

    assert (
        report["claims"][0].evidence[0]
        ["evidence_type"]
        == "architecture"
    )

    print(
        "Unified risk report contract passed."
    )


def test_real_repository_unified_risk_report():
    import json

    from llm.risk_report import build_risk_report

    with open(
        "artifacts/repository_analysis.json",
        "r",
        encoding="utf-8",
    ) as file:
        analysis = json.load(file)

    risk_signals = analysis["risk_signals"]

    report = build_risk_report(
        risk_signals
    )

    assert (
        report["risk_signal_count"]
        == len(risk_signals)
    )

    assert (
        report["claim_count"]
        == len(risk_signals)
    )

    assert (
        report["coverage"]["claim_count"]
        == len(risk_signals)
    )

    assert (
        report["coverage"]["supported_claims"]
        == len(risk_signals)
    )

    assert (
        report["coverage"]["unsupported_claims"]
        == 0
    )

    assert (
        report["coverage"]["coverage"]
        == 1.0
    )

    for claim in report["claims"]:
        assert claim.status == "possible_risk"
        assert len(claim.evidence) == 1
        assert (
            claim.evidence[0]["evidence_type"]
            == "architecture"
        )

    print(
        "Real repository unified risk report passed."
    )


def test_risk_claim_preserves_risk_explanation():
    from llm.risk_claims import build_risk_claim

    risk_signal = {
        "file": "src\\requests\\models.py",
        "module_name": "requests.models",
        "signal": "high_connectivity",
        "connection_count": 20,
        "incoming_count": 10,
        "outgoing_count": 10,
        "severity": "high",
        "status": "possible_risk",
        "reason": (
            "This module has 20 dependency connections "
            "(10 incoming and 10 outgoing). "
            "High connectivity may indicate that the "
            "module is highly coupled with other "
            "production modules."
        ),
        "evidence": {
            "file": "src\\requests\\models.py",
            "incoming_dependencies": [
                "requests.sessions"
            ],
            "outgoing_dependencies": [
                "requests.compat"
            ],
            "incoming_count": 10,
            "outgoing_count": 10,
            "total_connections": 20,
        },
    }

    claim = build_risk_claim(
        risk_signal
    )

    assert claim.status == "possible_risk"

    assert (
        "requests.models"
        in claim.text
    )

    assert (
        "20 dependency connections"
        in claim.text
    )

    assert (
        "High connectivity may indicate"
        in claim.text
    )

    assert len(claim.evidence) == 1

    assert (
        claim.evidence[0]["module_name"]
        == "requests.models"
    )

    print(
        "Risk claim explanation preservation passed."
    )


def test_risk_claim_preserves_severity():
    from llm.risk_claims import build_risk_claim

    risk_signal = {
        "file": "src\\requests\\models.py",
        "module_name": "requests.models",
        "signal": "high_connectivity",
        "connection_count": 20,
        "incoming_count": 10,
        "outgoing_count": 10,
        "severity": "high",
        "status": "possible_risk",
        "reason": (
            "This module has 20 dependency connections "
            "(10 incoming and 10 outgoing). "
            "High connectivity may indicate that the "
            "module is highly coupled with other "
            "production modules."
        ),
        "evidence": {
            "file": "src\\requests\\models.py",
            "incoming_dependencies": [
                "requests.sessions"
            ],
            "outgoing_dependencies": [
                "requests.compat"
            ],
            "incoming_count": 10,
            "outgoing_count": 10,
            "total_connections": 20,
        },
    }

    claim = build_risk_claim(
        risk_signal
    )

    assert hasattr(
        claim,
        "severity",
    )

    assert claim.severity == "high"

    print(
        "Risk claim severity preservation passed."
    )



def test_repository_qa_preserves_multi_component_evidence_attribution():
    from llm.fake_provider import FakeLLMProvider
    from llm.repository_qa import answer_repository_query

    chunks = [
        {
            "file": "src/requests/sessions.py",
            "start_line": 501,
            "end_line": 550,
            "content": "def prepare_request(self, request):\n    return request",
            "symbols": {
                "classes": [{"name": "Session"}],
                "functions": [{"name": "prepare_request"}],
            },
        },
        {
            "file": "src/requests/adapters.py",
            "start_line": 551,
            "end_line": 600,
            "content": "class HTTPAdapter: pass\n    def send(self, request): pass",
            "symbols": {
                "classes": [{"name": "HTTPAdapter"}],
                "functions": [{"name": "send"}],
            },
        },
    ]

    provider = FakeLLMProvider(
        "Requests uses Session objects to prepare requests, and "
        "HTTPAdapter handles connections and sending requests."
    )

    result = answer_repository_query(
        query="How do Sessions and adapters work in Requests?",
        chunks=chunks,
        provider=provider,
    )

    claim_files = {
        item["file"]
        for item in result["claims"][0].evidence
    }

    assert "src/requests/adapters.py" in claim_files
    assert "src/requests/sessions.py" in claim_files



if __name__ == "__main__":
    test_claim_contract()
    test_answer_backward_compatibility()
    test_answer_with_claims()
    test_answer_service_validates_evidence()
    test_multi_claim_decomposition_contract()
    test_multi_claims_have_independent_evidence()
    test_repository_qa_builds_multiple_claims()
    test_unknown_claim_has_no_evidence()
    test_claim_evidence_prefers_claim_relevant_architecture()
    test_claim_evidence_coverage()
    test_risk_signal_builds_evidence_backed_claim()
    test_risk_claims_have_full_evidence_coverage()
    test_unified_risk_report_contract()
    print("150C answer contract tests passed.")