from llm.claim_coverage import (
    calculate_claim_coverage,
)
from llm.risk_claims import (
    build_risk_claim,
)


def build_risk_report(
    risk_signals: list[dict],
) -> dict:
    """
    Build a unified evidence-backed risk report.

    Each deterministic risk signal becomes a
    POSSIBLE_RISK AnswerClaim with architecture
    evidence. The report also exposes claim-level
    evidence coverage.
    """

    if not isinstance(
        risk_signals,
        list,
    ):
        raise TypeError(
            "Risk signals must be a list."
        )

    claims = [
        build_risk_claim(signal)
        for signal in risk_signals
    ]

    coverage = calculate_claim_coverage(
        claims
    )

    return {
        "risk_signal_count": len(
            risk_signals
        ),
        "claim_count": len(claims),
        "claims": claims,
        "coverage": coverage,
    }