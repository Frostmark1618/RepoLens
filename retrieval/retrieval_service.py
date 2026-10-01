from retrieval.architecture_evidence import (
    retrieve_architecture_evidence,
)
from retrieval.retriever import (
    classify_query_intent,
    expand_with_neighboring_chunks,
    retrieve_chunks,
)


def retrieve_repository_evidence(
    query: str,
    chunks: list[dict],
    top_k: int = 5,
    max_neighbors: int = 1,
    architecture_snapshot: dict | None = None,
) -> dict:
    """
    Retrieve repository evidence for a user query.

    Primary evidence comes directly from retrieval.
    Supporting evidence comes from neighboring chunks
    in the same file.
    """

    results = retrieve_chunks(
        query,
        chunks,
        top_k=top_k,
    )

    expanded_results = expand_with_neighboring_chunks(
        results,
        chunks,
        max_neighbors=max_neighbors,
    )

    architecture_evidence = []

    query_intent = classify_query_intent(
        query
    )

    if (
        query_intent == "architecture"
        and architecture_snapshot is not None
    ):
        architecture_evidence = (
            retrieve_architecture_evidence(
                query,
                architecture_snapshot,
                top_k=top_k,
            )
        )

    evidence = []
    supporting_evidence = []

    for result in expanded_results:
        symbols = result.get(
            "symbols",
            {},
        )

        if not isinstance(symbols, dict):
            symbols = {}

        classes = symbols.get(
            "classes",
            [],
        )

        functions = symbols.get(
            "functions",
            [],
        )

        if not isinstance(classes, list):
            classes = []

        if not isinstance(functions, list):
            functions = []

        item = {
            "file": result["file"],
            "start_line": result["start_line"],
            "end_line": result["end_line"],
            "content": result["content"],
            "retrieval_score": result[
                "retrieval_score"
            ],
            "retrieval_role": result.get("retrieval_role", "supporting"),
            "context_role": result.get(
                "context_role",
                "retrieved",
            ),
            "symbols": {
                "classes": classes,
                "functions": functions,
            },
        }

        if item["context_role"] == "retrieved":
            evidence.append(item)
        else:
            supporting_evidence.append(item)

    return {
        "query": query,
        "result_count": len(evidence),
        "evidence": evidence,
        "supporting_evidence": supporting_evidence,
        "supporting_result_count": len(
            supporting_evidence
        ),
        "architecture_evidence": architecture_evidence,
        "architecture_result_count": len(
            architecture_evidence
        ),
    }