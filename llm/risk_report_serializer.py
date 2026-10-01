from llm.claims import AnswerClaim


def serialize_risk_report(
    risk_report: dict,
) -> dict:
    """
    Convert an in-memory unified risk report into
    JSON-serializable dashboard data.
    """

    if not isinstance(
        risk_report,
        dict,
    ):
        raise TypeError(
            "Risk report must be a dictionary."
        )

    claims = risk_report.get("claims")

    if not isinstance(
        claims,
        list,
    ):
        raise TypeError(
            "Risk report claims must be a list."
        )

    serialized_claims = []

    for claim in claims:
        if not isinstance(
            claim,
            AnswerClaim,
        ):
            raise TypeError(
                "Each risk report claim must be "
                "an AnswerClaim."
            )

        serialized_claims.append(
    {
        "text": claim.text,
        "status": claim.status,
        "category": claim.category,
        "severity": claim.severity,
        "evidence": claim.evidence,
    }
)

    coverage = risk_report.get(
        "coverage"
    )

    if not isinstance(
        coverage,
        dict,
    ):
        raise TypeError(
            "Risk report coverage must be a dictionary."
        )

    return {
        "risk_signal_count": risk_report[
            "risk_signal_count"
        ],
        "claim_count": risk_report[
            "claim_count"
        ],
        "claims": serialized_claims,
        "coverage": coverage,
    }