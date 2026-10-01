from llm.answer_service import (
    generate_repository_answer,
)
from llm.fake_provider import FakeLLMProvider


def test_invalid_evidence_is_rejected():
    context = "REPOSITORY EVIDENCE"

    invalid_evidence = [
        {
            "evidence_type": "invalid",
            "file": "src/requests/sessions.py",
        }
    ]

    try:
        generate_repository_answer(
            "test",
            context,
            FakeLLMProvider("FACT: test"),
            evidence=invalid_evidence,
        )
    except ValueError as error:
        assert str(error) == (
            "Evidence type must be "
            "'code' or 'architecture'."
        )
        print(
            "Validation error:",
            error,
        )
    else:
        raise AssertionError(
            "Invalid evidence was accepted"
        )


if __name__ == "__main__":
    test_invalid_evidence_is_rejected()
    print(
        "Evidence validation protection test passed."
    )