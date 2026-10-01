from dataclasses import dataclass, field

from llm.claims import AnswerClaim


@dataclass
class EvidenceReference:
    """
    A structured reference to repository evidence.
    """

    evidence_type: str
    file: str | None = None
    start_line: int | None = None
    end_line: int | None = None
    module_name: str | None = None


@dataclass
class RepoAnswer:
    """
    Structured RepoLens answer.

    The original answer/status/evidence contract is
    preserved while supporting claim-level evidence.
    """

    answer: str
    status: str
    evidence: list[dict] = field(
        default_factory=list
    )
    claims: list[AnswerClaim] = field(
        default_factory=list
    )


def build_answer(
    answer: str,
    status: str,
    evidence: list[dict] | None = None,
    claims: list[AnswerClaim] | None = None,
) -> dict:
    """
    Build a structured RepoLens answer.

    Backward-compatible with the original
    answer/status/evidence contract.
    """

    if not isinstance(answer, str):
        raise TypeError(
            "Answer must be a string."
        )

    if not isinstance(status, str):
        raise TypeError(
            "Status must be a string."
        )

    allowed_statuses = {
        "fact",
        "inference",
        "possible_risk",
        "unknown",
    }

    normalized_status = status.lower().strip()

    if normalized_status not in allowed_statuses:
        raise ValueError(
            "Status must be one of: "
            "fact, inference, possible_risk, unknown."
        )

    if evidence is None:
        evidence = []

    if not isinstance(evidence, list):
        raise TypeError(
            "Evidence must be a list."
        )

    if claims is None:
        claims = []

    if not isinstance(claims, list):
        raise TypeError(
            "Claims must be a list."
        )

    for claim in claims:
        if not isinstance(claim, AnswerClaim):
            raise TypeError(
                "Every claim must be an AnswerClaim."
            )

    return {
        "answer": answer,
        "status": normalized_status,
        "evidence": evidence,
        "claims": claims,
    }