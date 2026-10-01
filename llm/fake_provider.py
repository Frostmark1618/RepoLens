from llm.base import LLMProvider


class FakeLLMProvider(LLMProvider):
    """
    Deterministic provider used for local testing.

    Normal answer-generation calls return the configured response.
    Claim-verification calls return a structured supported decision so
    repository-QA tests can exercise evidence attribution without requiring
    a real LLM or relying on provider-specific JSON behavior.
    """

    def __init__(
        self,
        response: str = "FAKE LLM RESPONSE",
    ):
        self.response = response

    def generate(
        self,
        prompt: str,
    ) -> str:
        if not isinstance(prompt, str):
            raise TypeError(
                "Prompt must be a string."
            )

        lowered = prompt.lower()

        if (
            "strict evidence verifier" in lowered
            or "return exactly:" in lowered
            and '"decision"' in lowered
            and "evidence" in lowered
        ):
            return (
                '{"decision":"supported",'
                '"reason":"Supported by the supplied test evidence."}'
            )

        return self.response
