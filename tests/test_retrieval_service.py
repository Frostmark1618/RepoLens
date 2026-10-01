from retrieval.retrieval_service import (
    retrieve_repository_evidence,
)


def main():
    chunks = [
        {
            "file": "src/requests/adapters.py",
            "extension": ".py",
            "start_line": 1,
            "end_line": 20,
            "content": (
                "class HTTPAdapter:\n"
                "    def send(self, request):\n"
                "        return self.session.send(request)"
            ),
        },
        {
            "file": "tests/test_adapters.py",
            "extension": ".py",
            "start_line": 1,
            "end_line": 20,
            "content": (
                "def test_adapter():\n"
                "    adapter = HTTPAdapter()"
            ),
        },
    ]

    result = retrieve_repository_evidence(
        "HTTPAdapter send request",
        chunks,
        top_k=1,
    )

    assert result["query"] == (
        "HTTPAdapter send request"
    )

    assert result["result_count"] == 1

    assert len(result["evidence"]) == 1

    evidence = result["evidence"][0]

    assert (
        evidence["file"]
        == "src/requests/adapters.py"
    )

    assert evidence["start_line"] == 1
    assert evidence["end_line"] == 20
    assert "HTTPAdapter" in evidence["content"]

    assert (
        "retrieval_score"
        in evidence
    )

    print("Retrieval service verification passed.")
    print(
        f"Evidence results: "
        f"{result['result_count']}"
    )
    print(
        f"Top evidence: "
        f"{evidence['file']}:"
        f"{evidence['start_line']}-"
        f"{evidence['end_line']}"
    )

def test_architecture_evidence_integration():
    import json

    with open(
        "artifacts/repository_chunks.json",
        encoding="utf-8",
    ) as file:
        chunks = json.load(file)

    with open(
        "artifacts/architecture_snapshot.json",
        encoding="utf-8",
    ) as file:
        snapshot = json.load(file)

    result = retrieve_repository_evidence(
        "session dependencies",
        chunks,
        top_k=5,
        architecture_snapshot=snapshot,
    )

    assert result["query"] == (
        "session dependencies"
    )

    assert result["result_count"] == 3

    assert result[
        "architecture_result_count"
    ] == 1

    architecture_evidence = result[
        "architecture_evidence"
    ]

    assert (
        architecture_evidence[0][
            "module_name"
        ]
        == "requests.sessions"
    )

    assert (
        architecture_evidence[0][
            "outgoing_count"
        ]
        == 12
    )

    assert (
        architecture_evidence[0][
            "incoming_count"
        ]
        == 2
    )

    assert (
        architecture_evidence[0][
            "total_connections"
        ]
        == 14
    )

    assert (
        architecture_evidence[0]["status"]
        == "fact"
    )

    print(
        "Architecture evidence integration "
        "test passed."
    )





if __name__ == "__main__":
    main()
    test_architecture_evidence_integration()