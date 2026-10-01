import os


DEFAULT_LLM_PROVIDER = "ollama"
DEFAULT_LLM_MODEL = "qwen2.5-coder:7b"
DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_GEMINI_MODEL = "gemini-3.8-flash"
DEFAULT_GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_LLM_TIMEOUT_SECONDS = 120


def _positive_int(value: str | None, default: int) -> int:
    try:
        parsed = int(value or default)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def get_llm_settings() -> dict:
    """Load server-side LLM configuration without exposing secrets to clients."""
    provider = os.getenv("LLM_PROVIDER", DEFAULT_LLM_PROVIDER).strip().lower()
    default_model = DEFAULT_GEMINI_MODEL if provider == "gemini" else DEFAULT_LLM_MODEL
    return {
        "provider": provider,
        "model": os.getenv("LLM_MODEL", default_model).strip() or default_model,
        "ollama_base_url": os.getenv("OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE_URL).strip()
        or DEFAULT_OLLAMA_BASE_URL,
        "gemini_api_key": os.getenv("GEMINI_API_KEY", "").strip(),
        "gemini_base_url": os.getenv("GEMINI_BASE_URL", DEFAULT_GEMINI_BASE_URL).strip()
        or DEFAULT_GEMINI_BASE_URL,
        "timeout": _positive_int(
            os.getenv("LLM_TIMEOUT_SECONDS"),
            DEFAULT_LLM_TIMEOUT_SECONDS,
        ),
    }
