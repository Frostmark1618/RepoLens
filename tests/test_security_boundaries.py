from fastapi.testclient import TestClient
import pytest

from api.main import app
from ingestion.github_loader import clone_repository


def test_github_loader_rejects_non_github_urls():
    with pytest.raises(ValueError):
        clone_repository(
            "https://example.com/org/repo.git",
            "repo",
        )


def test_github_loader_rejects_path_traversal_repository_name():
    with pytest.raises(ValueError):
        clone_repository(
            "https://github.com/psf/requests.git",
            "../repo",
        )


def test_health_exposes_security_headers():
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert response.headers["Cache-Control"] == "no-store"


def test_ask_hides_internal_provider_errors(
    monkeypatch,
):
    def failing_ask(*args, **kwargs):
        raise ConnectionError(
            "Local Ollama provider is unavailable."
        )

    monkeypatch.setattr(
        "api.main.repository_service.ask",
        failing_ask,
    )

    response = TestClient(app).post(
        "/api/repository/ask",
        json={"query": "capital of Japan"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Local LLM provider is unavailable."
    )

    assert "Traceback" not in response.text
    assert "localhost:11434" not in response.text