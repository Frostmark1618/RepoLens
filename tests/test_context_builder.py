from retrieval.context_builder import (
    build_rag_context,
)


def main():
    retrieval_result = {
        "query": "HTTPAdapter send request",
        "result_count": 2,
        "evidence": [
            {
                "file": "src/requests/adapters.py",
                "start_line": 1,
                "end_line": 20,
                "retrieval_score": 0.8,
                "content": (
                    "class HTTPAdapter:\n"
                    "    def send(self, request):"
                ),
            },
            {
                "file": "src/requests/sessions.py",
                "start_line": 100,
                "end_line": 120,
                "retrieval_score": 0.6,
                "content": (
                    "session.send(request)"
                ),
            },
        ],
    }

    context = build_rag_context(
        retrieval_result
    )

    assert "REPOSITORY EVIDENCE" in context

    assert (
        "User Query: HTTPAdapter send request"
        in context
    )

    assert "[Primary Evidence 1]" in context
    assert "[Primary Evidence 2]" in context

    assert (
        "src/requests/adapters.py"
        in context
    )

    assert (
        "lines 1-20"
        in context
    )

    assert (
        "Retrieval Score: 0.8"
        in context
    )

    assert (
        "class HTTPAdapter:"
        in context
    )

    assert (
        "src/requests/sessions.py"
        in context
    )

    assert (
        "session.send(request)"
        in context
    )

    # Empty evidence case
    empty_result = {
        "query": "unknown repository concept",
        "result_count": 0,
        "evidence": [],
    }

    empty_context = build_rag_context(
        empty_result
    )

    assert (
        "No repository evidence was retrieved"
        in empty_context
    )

    print("Context builder verification passed.")
    print("Evidence sections: 2")
    print("Empty evidence case: handled")


if __name__ == "__main__":
    main()