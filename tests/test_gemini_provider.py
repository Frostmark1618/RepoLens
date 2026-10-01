import json

import pytest

from llm.gemini_provider import GeminiProvider


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception("request failed")

    def json(self):
        return self._payload


def make_provider():
    return GeminiProvider(
        model="gemini-3.8-flash",
        api_key="test-key",
        base_url="https://example.invalid/v1beta",
        timeout=5,
    )


def test_generate_extracts_text(monkeypatch):
    provider = make_provider()

    def fake_post(*args, **kwargs):
        assert kwargs["headers"]["x-goog-api-key"] == "test-key"
        assert kwargs["json"]["contents"][0]["parts"][0]["text"] == "hello"
        return FakeResponse(
            {"candidates": [{"content": {"parts": [{"text": "answer"}]}}]}
        )

    monkeypatch.setattr("llm.gemini_provider.requests.post", fake_post)
    assert provider.generate("hello") == "answer"


def test_generate_json_sends_structured_schema(monkeypatch):
    provider = make_provider()
    schema = {"type": "object", "properties": {"answer": {"type": "string"}}}

    def fake_post(*args, **kwargs):
        config = kwargs["json"]["generationConfig"]
        assert config["responseMimeType"] == "application/json"
        assert config["responseSchema"] == schema
        return FakeResponse(
            {"candidates": [{"content": {"parts": [{"text": json.dumps({"answer": "ok"})}]}}]}
        )

    monkeypatch.setattr("llm.gemini_provider.requests.post", fake_post)
    assert provider.generate_json("hello", schema) == '{"answer": "ok"}'


def test_empty_api_key_rejected():
    with pytest.raises(ValueError, match="API key is required"):
        GeminiProvider(api_key="")
