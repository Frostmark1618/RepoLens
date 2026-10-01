import os

import requests

from llm.base import LLMProvider


class GeminiProvider(LLMProvider):
    """Server-side Google Gemini provider using the official REST API."""

    def __init__(
        self,
        model: str = "gemini-3.8-flash",
        api_key: str | None = None,
        base_url: str = "https://generativelanguage.googleapis.com/v1beta",
        timeout: int = 120,
        temperature: float = 0.0,
    ):
        if not isinstance(model, str) or not model.strip():
            raise ValueError("Model must be a non-empty string.")
        if not isinstance(api_key, str) or not api_key.strip():
            raise ValueError("Gemini API key is required.")
        if not isinstance(base_url, str) or not base_url.strip():
            raise ValueError("Base URL must be a non-empty string.")
        if not isinstance(timeout, int) or timeout <= 0:
            raise ValueError("Timeout must be a positive integer.")
        if not isinstance(temperature, (int, float)):
            raise TypeError("Temperature must be numeric.")
        if not 0 <= float(temperature) <= 2:
            raise ValueError("Temperature must be between 0 and 2.")

        self.model = model.strip()
        self.api_key = api_key.strip()
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.temperature = float(temperature)

    def _post(self, payload: dict) -> dict:
        try:
            response = requests.post(
                f"{self.base_url}/models/{self.model}:generateContent",
                headers={
                    "x-goog-api-key": self.api_key,
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.Timeout as exc:
            raise ConnectionError("Gemini provider timed out.") from exc
        except requests.exceptions.ConnectionError as exc:
            raise ConnectionError("Gemini provider is unavailable.") from exc
        except requests.exceptions.RequestException as exc:
            raise ConnectionError("Gemini provider request failed.") from exc
        except ValueError as exc:
            raise ValueError("Gemini returned invalid JSON.") from exc

        if not isinstance(data, dict):
            raise ValueError("Gemini response must be a JSON object.")
        return data

    @staticmethod
    def _extract_text(data: dict) -> str:
        candidates = data.get("candidates")
        if not isinstance(candidates, list) or not candidates:
            raise ValueError("Gemini response does not contain candidates.")

        candidate = candidates[0]
        content = candidate.get("content") if isinstance(candidate, dict) else None
        parts = content.get("parts") if isinstance(content, dict) else None
        if not isinstance(parts, list):
            raise ValueError("Gemini response does not contain valid content.")

        text_parts = [
            part.get("text")
            for part in parts
            if isinstance(part, dict) and isinstance(part.get("text"), str)
        ]
        answer = "".join(text_parts).strip()
        if not answer:
            raise ValueError("Gemini response does not contain valid text.")
        return answer

    def generate(self, prompt: str) -> str:
        if not isinstance(prompt, str):
            raise TypeError("Prompt must be a string.")
        if not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        data = self._post(
            {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": self.temperature},
            }
        )
        return self._extract_text(data)

    def generate_json(self, prompt: str, schema: dict) -> str:
        if not isinstance(prompt, str):
            raise TypeError("Prompt must be a string.")
        if not prompt.strip():
            raise ValueError("Prompt cannot be empty.")
        if not isinstance(schema, dict):
            raise TypeError("Schema must be a dictionary.")

        data = self._post(
            {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0,
                    "responseMimeType": "application/json",
                    "responseSchema": schema,
                },
            }
        )
        return self._extract_text(data)

    def health(self, timeout: int = 5) -> dict:
        """Return non-secret readiness information for the configured model."""
        try:
            response = requests.get(
                f"{self.base_url}/models/{self.model}",
                headers={"x-goog-api-key": self.api_key},
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

        configured_model = data.get("name") if isinstance(data, dict) else None
        return {
            "reachable": True,
            "model_configured": bool(configured_model),
            "model": self.model,
        }
