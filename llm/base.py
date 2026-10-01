from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """
    Provider-independent interface for LLM backends.
    """

    @abstractmethod
    def generate(
        self,
        prompt: str,
    ) -> str:
        """
        Generate a text response from a prompt.
        """
        raise NotImplementedError

    def generate_json(
        self,
        prompt: str,
        schema: dict,
    ) -> str:
        """
        Generate a JSON response matching the requested schema when the
        provider supports structured output.

        Providers without native structured output keep backward-compatible
        behavior by falling back to normal text generation; callers still
        validate the returned JSON independently.
        """
        if not isinstance(prompt, str):
            raise TypeError("Prompt must be a string.")
        if not isinstance(schema, dict):
            raise TypeError("Schema must be a dictionary.")
        return self.generate(prompt)
