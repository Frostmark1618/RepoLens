from retrieval.retriever import (
    tokenize,
    score_chunk,
    retrieve_chunks,
)


def main():
    # Tokenization
    tokens = tokenize(
        "How does the HTTP adapter handle requests?"
    )

    assert "http" in tokens
    assert "adapter" in tokens
    assert "requests" in tokens
    assert "the" not in tokens

    # Synthetic repository chunks
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
            "file": "src/requests/models.py",
            "extension": ".py",
            "start_line": 1,
            "end_line": 20,
            "content": (
                "class Request:\n"
                "    def __init__(self, method, url):\n"
                "        self.method = method"
            ),
        },
        {
            "file": "tests/test_models.py",
            "extension": ".py",
            "start_line": 1,
            "end_line": 20,
            "content": (
                "def test_request_model():\n"
                "    request = Request('GET', '/')"
            ),
        },
    ]

    # Score check
    adapter_score = score_chunk(
        "HTTPAdapter send request",
        chunks[0],
    )

    models_score = score_chunk(
        "HTTPAdapter send request",
        chunks[1],
    )

    assert adapter_score > models_score

    # Retrieval check
    results = retrieve_chunks(
        "HTTPAdapter send request",
        chunks,
        top_k=2,
    )

    assert len(results) == 2

    assert (
        results[0]["file"]
        == "src/requests/adapters.py"
    )

    assert "retrieval_score" in results[0]

    assert (
        results[0]["retrieval_score"]
        >= results[1]["retrieval_score"]
    )

    # Evidence metadata must be preserved
    assert results[0]["start_line"] == 1
    assert results[0]["end_line"] == 20
    assert "HTTPAdapter" in results[0]["content"]

    print("Retriever verification passed.")
    print(
        f"Top result: {results[0]['file']}"
    )
    print(
        f"Top score: "
        f"{results[0]['retrieval_score']}"
    )

def test_neighboring_chunk_expansion():
    from retrieval.retriever import (
        expand_with_neighboring_chunks,
    )

    chunks = [
        {
            "file": "src/example.py",
            "start_line": 1,
            "end_line": 50,
            "content": "chunk one",
            "symbols": {},
        },
        {
            "file": "src/example.py",
            "start_line": 51,
            "end_line": 100,
            "content": "chunk two",
            "symbols": {},
        },
        {
            "file": "src/example.py",
            "start_line": 101,
            "end_line": 150,
            "content": "chunk three",
            "symbols": {},
        },
        {
            "file": "src/other.py",
            "start_line": 1,
            "end_line": 50,
            "content": "other file",
            "symbols": {},
        },
    ]

    retrieved = [
        {
            "file": "src/example.py",
            "start_line": 51,
            "end_line": 100,
            "content": "chunk two",
            "symbols": {},
            "retrieval_score": 0.8,
        }
    ]

    expanded = expand_with_neighboring_chunks(
        retrieved,
        chunks,
        max_neighbors=1,
    )

    assert len(expanded) == 3

    roles = {
        item["context_role"]
        for item in expanded
    }

    assert roles == {
        "retrieved",
        "neighbor",
    }

    retrieved_items = [
        item
        for item in expanded
        if item["context_role"] == "retrieved"
    ]

    assert len(retrieved_items) == 1
    assert retrieved_items[0]["retrieval_score"] == 0.8

    neighbor_items = [
        item
        for item in expanded
        if item["context_role"] == "neighbor"
    ]

    assert len(neighbor_items) == 2

    for item in neighbor_items:
        assert item["retrieval_score"] == 0.4


def test_query_intent_classification():
    from retrieval.retriever import classify_query_intent

    test_cases = [
        ("FlaskyStyle", "symbol"),
        ("HTTPAdapter class", "symbol"),
        ("prepare request", "implementation"),
        ("how does session send request", "implementation"),
        ("HTTP adapter", "concept"),
        ("session dependencies", "architecture"),
    ]

    for query, expected_intent in test_cases:
        actual_intent = classify_query_intent(query)

        assert actual_intent == expected_intent, (
            f"Query: {query!r}, "
            f"Expected: {expected_intent!r}, "
            f"Got: {actual_intent!r}"
        )


def test_architecture_query_prioritizes_production_evidence():
    import json

    from retrieval.retriever import (
        retrieve_chunks,
    )

    with open(
        "artifacts/repository_chunks.json",
        encoding="utf-8",
    ) as file:
        chunks = json.load(file)

    results = retrieve_chunks(
        "session dependencies",
        chunks,
        top_k=5,
    )

    production_positions = [
        index
        for index, result in enumerate(results)
        if result["file"].startswith(
            "src\\"
        )
    ]

    assert production_positions, (
        "Expected production evidence "
        "for architecture query."
    )

    assert production_positions[0] == 0, (
        "Production architecture evidence "
        "should rank first."
    )


if __name__ == "__main__":
    main()