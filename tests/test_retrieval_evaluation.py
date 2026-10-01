import json

from retrieval.retriever import retrieve_chunks


def load_chunks():
    with open(
        "artifacts/repository_chunks.json",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def calculate_metrics(
    results: list[dict],
    expected_files: set[str],
):
    retrieved_files = {
        result["file"]
        for result in results
    }

    hits = retrieved_files & expected_files

    precision = (
        len(hits) / len(retrieved_files)
        if retrieved_files
        else 0.0
    )

    recall = (
        len(hits) / len(expected_files)
        if expected_files
        else 0.0
    )

    hit_rate = 1.0 if hits else 0.0

    return {
        "precision": precision,
        "recall": recall,
        "hit_rate": hit_rate,
        "hits": hits,
    }


def test_http_request_retrieval():
    chunks = load_chunks()

    query = "How does requests send an HTTP request?"

    expected_files = {
        "src\\requests\\adapters.py",
        "src\\requests\\sessions.py",
        "src\\requests\\api.py",
    }

    results = retrieve_chunks(
        query,
        chunks,
        top_k=5,
    )

    metrics = calculate_metrics(
        results,
        expected_files,
    )

    assert metrics["recall"] == 1.0
    assert metrics["hit_rate"] == 1.0

    print("\nHTTP Request Retrieval")
    print("Precision@5:", round(metrics["precision"], 3))
    print("Recall@5:", round(metrics["recall"], 3))
    print("Hit Rate@5:", round(metrics["hit_rate"], 3))


def test_authentication_retrieval():
    chunks = load_chunks()

    query = "How does requests handle authentication?"

    expected_files = {
        "src\\requests\\auth.py",
    }

    results = retrieve_chunks(
        query,
        chunks,
        top_k=5,
    )

    metrics = calculate_metrics(
        results,
        expected_files,
    )

    assert metrics["hit_rate"] == 1.0

    print("\nAuthentication Retrieval")
    print("Precision@5:", round(metrics["precision"], 3))
    print("Recall@5:", round(metrics["recall"], 3))
    print("Hit Rate@5:", round(metrics["hit_rate"], 3))


def test_session_retrieval():
    chunks = load_chunks()

    query = "How does the requests session work?"

    expected_files = {
        "src\\requests\\sessions.py",
    }

    results = retrieve_chunks(
        query,
        chunks,
        top_k=5,
    )

    metrics = calculate_metrics(
        results,
        expected_files,
    )

    assert metrics["hit_rate"] == 1.0

    print("\nSession Retrieval")
    print("Precision@5:", round(metrics["precision"], 3))
    print("Recall@5:", round(metrics["recall"], 3))
    print("Hit Rate@5:", round(metrics["hit_rate"], 3))


def test_unrelated_query_returns_no_results():
    chunks = load_chunks()

    query = "What is the capital of Japan?"

    results = retrieve_chunks(
        query,
        chunks,
        top_k=5,
    )

    assert results == []

    print("\nUnrelated Query")
    print("Retrieved results:", len(results))
    print("Status: correctly rejected")