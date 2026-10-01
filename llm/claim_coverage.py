def calculate_claim_coverage(
    claims: list,
) -> dict:
    """
    Calculate deterministic evidence coverage
    across repository answer claims.

    A claim is considered supported when:
        - its status is not unknown
        - it has at least one evidence item

    UNKNOWN claims are considered unsupported because
    they explicitly state that repository evidence does
    not establish the answer.
    """

    if not isinstance(claims, list):
        raise TypeError(
            "Claims must be a list."
        )

    total_claims = len(claims)

    supported_claims = 0
    unsupported_claims = 0

    for claim in claims:
        if not hasattr(claim, "status"):
            raise TypeError(
                "Each claim must have a status attribute."
            )

        if not hasattr(claim, "evidence"):
            raise TypeError(
                "Each claim must have an evidence attribute."
            )

        if (
            claim.status != "unknown"
            and len(claim.evidence) > 0
        ):
            supported_claims += 1
        else:
            unsupported_claims += 1

    if total_claims == 0:
        coverage = 0.0
    else:
        coverage = (
            supported_claims / total_claims
        )

    return {
        "claim_count": total_claims,
        "supported_claims": supported_claims,
        "unsupported_claims": unsupported_claims,
        "coverage": round(coverage, 4),
    }