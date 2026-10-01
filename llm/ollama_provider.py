import requests

from llm.base import LLMProvider


class OllamaProvider(LLMProvider):
    """
    Server-side Ollama-backed LLM provider.

    Ollama is never contacted by the browser. The FastAPI backend owns this
    connection, which keeps the local/provider endpoint out of the public
    frontend boundary.
    """

    def __init__(
        self,
        model: str = "qwen2.5-coder:7b",
        base_url: str = "http://localhost:11434",
        timeout: int = 120,
        temperature: float = 0.0,
    ):
        if not isinstance(model, str) or not model.strip():
            raise ValueError("Model must be a non-empty string.")
        if not isinstance(base_url, str) or not base_url.strip():
            raise ValueError("Base URL must be a non-empty string.")
        if not isinstance(timeout, int) or timeout <= 0:
            raise ValueError("Timeout must be a positive integer.")
        if not isinstance(temperature, (int, float)):
            raise TypeError("Temperature must be numeric.")
        if not 0 <= float(temperature) <= 2:
            raise ValueError("Temperature must be between 0 and 2.")

        self.model = model.strip()
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.temperature = float(temperature)

    def _post_generate(self, payload: dict) -> dict:
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.Timeout as exc:
            raise ConnectionError("Local Ollama provider timed out.") from exc
        except requests.exceptions.ConnectionError as exc:
            raise ConnectionError("Local Ollama provider is unavailable.") from exc
        except requests.exceptions.RequestException as exc:
            raise ConnectionError("Local Ollama provider request failed.") from exc
        except ValueError as exc:
            raise ValueError("Ollama returned invalid JSON.") from exc

        if not isinstance(data, dict):
            raise ValueError("Ollama response must be a JSON object.")
        return data

    def generate(self, prompt: str) -> str:
        if not isinstance(prompt, str):
            raise TypeError("Prompt must be a string.")
        if not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        data = self._post_generate(
            {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": self.temperature},
            }
        )
        answer = data.get("response")
        if not isinstance(answer, str):
            raise ValueError("Ollama response does not contain valid text.")
        return answer.strip()

    def generate_json(self, prompt: str, schema: dict) -> str:
        if not isinstance(prompt, str):
            raise TypeError("Prompt must be a string.")
        if not prompt.strip():
            raise ValueError("Prompt cannot be empty.")
        if not isinstance(schema, dict):
            raise TypeError("Schema must be a dictionary.")

        data = self._post_generate(
            {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "format": schema,
                "options": {"temperature": 0},
            }
        )
        answer = data.get("response")
        if not isinstance(answer, str):
            raise ValueError("Ollama structured response does not contain valid text.")
        return answer.strip()

    def health(self, timeout: int = 3) -> dict:
        """Return a non-secret readiness snapshot for the configured Ollama server."""
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=timeout,
            )
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.Timeout:
            return {"reachable": False, "reason": "timeout"}
        except requests.exceptions.ConnectionError:
            return {"reachable": False, "reason": "unavailable"}
        except requests.exceptions.RequestException:
            return {"reachable": False, "reason": "request_failed"}
        except ValueError:
            return {"reachable": False, "reason": "invalid_response"}

        models = data.get("models", []) if isinstance(data, dict) else []
        model_names = {
            item.get("name")
            for item in models
            if isinstance(item, dict) and isinstance(item.get("name"), str)
        }
        return {
            "reachable": True,
            "model_configured": self.model in model_names,
            "model": self.model,
        }
