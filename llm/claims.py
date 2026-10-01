from dataclasses import dataclass, field


@dataclass
class AnswerClaim:
    """
    A single factual or inferred claim made by RepoLens.
    """

    text: str
    status: str
    evidence: list[dict] = field(
        default_factory=list
    )

    def __post_init__(self):
        if not isinstance(self.text, str):
            raise TypeError(
                "Claim text must be a string."
            )

        if not self.text.strip():
            raise ValueError(
                "Claim text cannot be empty."
            )

        if not isinstance(self.status, str):
            raise TypeError(
                "Claim status must be a string."
            )

        allowed_statuses = {
            "fact",
            "inference",
            "possible_risk",
            "unknown",
        }

        normalized_status = (
            self.status.lower().strip()
        )

        if normalized_status not in allowed_statuses:
            raise ValueError(
                "Claim status must be one of: "
                "fact, inference, possible_risk, "
                "unknown."
            )

        if not isinstance(self.evidence, list):
            raise TypeError(
                "Claim evidence must be a list."
            )

        self.status = normalized_status