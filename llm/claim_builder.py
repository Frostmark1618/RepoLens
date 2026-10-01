from llm.claims import AnswerClaim


def build_answer_claim(
    answer: str,
    status: str,
    evidence: list[dict],
) -> AnswerClaim:
    """
    Build a claim representing the complete
    answer and attach the validated repository
    evidence supporting the answer.
    """

    if not isinstance(answer, str):
        raise TypeError(
            "Answer must be a string."
        )

    if not answer.strip():
        raise ValueError(
            "Answer cannot be empty."
        )

    if not isinstance(evidence, list):
        raise TypeError(
            "Evidence must be a list."
        )

    return AnswerClaim(
        text=answer,
        status=status,
        evidence=evidence,
    )