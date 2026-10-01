import os
import threading
import time

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.repository_service import RepositoryService
from config.llm_settings import get_llm_settings
from llm.gemini_provider import GeminiProvider
from llm.ollama_provider import OllamaProvider


app = FastAPI(
    title="RepoLens API",
    version="1.0.0",
    description=(
        "Evidence-based codebase intelligence "
        "and architecture drift auditor."
    ),
)


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------
# Development frontend:
# http://localhost:3000
#
# Backend:
# http://127.0.0.1:8000
#
# Keep origins explicit rather than allowing every origin.

def get_cors_origins() -> list[str]:
    raw = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    )
    origins = [
        item.strip().rstrip("/")
        for item in raw.split(",")
        if item.strip()
    ]
    if "*" in origins:
        raise RuntimeError(
            "CORS_ORIGINS must contain explicit origins; '*' is not allowed "
            "when credentials are enabled."
        )
    return origins or [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_size_guard(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > 256 * 1024:
                return JSONResponse(
                    status_code=413,
                    content={"detail": "Request body is too large."},
                )
        except ValueError:
            return JSONResponse(
                status_code=400,
                content={"detail": "Invalid Content-Length header."},
            )
    return await call_next(request)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Cache-Control"] = "no-store"
    return response


# ---------------------------------------------------------
# Services
# ---------------------------------------------------------

repository_service = RepositoryService()
llm_settings = get_llm_settings()

ollama_provider = OllamaProvider(
    model=llm_settings["model"] if llm_settings["provider"] == "ollama" else "qwen2.5-coder:7b",
    base_url=llm_settings["ollama_base_url"],
    timeout=llm_settings["timeout"],
)

gemini_provider = None
if llm_settings["provider"] == "gemini":
    if not llm_settings["gemini_api_key"]:
        raise RuntimeError(
            "GEMINI_API_KEY is required when LLM_PROVIDER=gemini."
        )
    gemini_provider = GeminiProvider(
        model=llm_settings["model"],
        api_key=llm_settings["gemini_api_key"],
        base_url=llm_settings["gemini_base_url"],
        timeout=llm_settings["timeout"],
    )

if llm_settings["provider"] == "ollama":
    active_llm_provider = ollama_provider
elif llm_settings["provider"] == "gemini":
    active_llm_provider = gemini_provider
else:
    raise RuntimeError(
        "Unsupported LLM_PROVIDER. Use 'ollama' or 'gemini'."
    )


# ---------------------------------------------------------
# Request Models
# ---------------------------------------------------------

class RepositoryQuestionRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Repository-related question.",
    )


# ---------------------------------------------------------
# Health
# ---------------------------------------------------------

@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "RepoLens",
    }


@app.get("/health/release")
def release_health() -> dict:
    """Expose a non-secret release identifier to detect frontend/backend drift."""
    return {
        "service": "RepoLens",
        "release": os.getenv(
            "REPOLENS_RELEASE_ID",
            "2026-09-30-final",
        ),
        "api_version": app.version,
        "qa_endpoint": "/api/repository/ask",
    }


@app.get("/health/llm")
def llm_health() -> dict:
    """Expose server-side LLM readiness without returning provider secrets."""
    status = active_llm_provider.health()
    if not status["reachable"]:
        return {
            "status": "unavailable",
            "provider": llm_settings["provider"],
            "model": llm_settings["model"],
            "reason": status["reason"],
        }

    if not status["model_configured"]:
        return {
            "status": "model_missing",
            "provider": llm_settings["provider"],
            "model": llm_settings["model"],
        }

    return {
        "status": "ready",
        "provider": llm_settings["provider"],
        "model": llm_settings["model"],
    }


# ---------------------------------------------------------
# Repository Overview
# ---------------------------------------------------------

@app.get("/api/repository/overview")
def repository_overview() -> dict:
    try:
        return repository_service.get_repository_overview()

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail="Repository analysis artifact is unavailable.",
        ) from error

    except ValueError as error:
        raise HTTPException(
            status_code=500,
            detail="Repository analysis could not be loaded.",
        ) from error


# ---------------------------------------------------------
# Complete Repository Analysis
# ---------------------------------------------------------

@app.get("/api/repository/analysis")
def repository_analysis() -> dict:
    try:
        return repository_service.get_repository_analysis()

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail="Repository analysis artifact is unavailable.",
        ) from error

    except ValueError as error:
        raise HTTPException(
            status_code=500,
            detail="Repository analysis could not be loaded.",
        ) from error


# ---------------------------------------------------------
# Architecture Drift
# ---------------------------------------------------------

@app.get("/api/repository/drift")
def repository_drift() -> dict:
    try:
        return repository_service.get_repository_drift()
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail="Architecture drift artifacts are unavailable.") from error
    except ValueError as error:
        raise HTTPException(status_code=500, detail="Unable to load architecture drift data.") from error


# ---------------------------------------------------------
# Repository Q&A
# ---------------------------------------------------------

def _positive_env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    try:
        value = int(raw) if raw is not None else default
    except (TypeError, ValueError):
        return default
    return value if value > 0 else default


QA_CONCURRENCY_LIMIT = _positive_env_int("REPOLENS_QA_CONCURRENCY", 2)
QA_RATE_LIMIT_PER_MINUTE = _positive_env_int("REPOLENS_QA_RATE_LIMIT_PER_MINUTE", 20)
qa_semaphore = threading.BoundedSemaphore(QA_CONCURRENCY_LIMIT)
qa_rate_lock = threading.Lock()
qa_rate_window: dict[str, list[float]] = {}


def _qa_rate_limited(client_host: str) -> bool:
    now = time.monotonic()
    window_start = now - 60.0
    with qa_rate_lock:
        timestamps = [
            value
            for value in qa_rate_window.get(client_host, [])
            if value > window_start
        ]
        if len(timestamps) >= QA_RATE_LIMIT_PER_MINUTE:
            qa_rate_window[client_host] = timestamps
            return True
        timestamps.append(now)
        qa_rate_window[client_host] = timestamps
        # Bound memory if many unique clients hit the endpoint.
        if len(qa_rate_window) > 5000:
            oldest = sorted(
                qa_rate_window.items(),
                key=lambda item: item[1][-1] if item[1] else 0.0,
            )[:1000]
            for key, _ in oldest:
                qa_rate_window.pop(key, None)
        return False

@app.post("/api/repository/ask")
def repository_ask(
    request: RepositoryQuestionRequest,
    http_request: Request,
) -> dict:
    """
    Answer a repository-aware question using the existing
    RepoLens retrieval, evidence, claim, and server-side LLM pipeline.
    """

    client_host = http_request.client.host if http_request.client else "unknown"
    if _qa_rate_limited(client_host):
        raise HTTPException(
            status_code=429,
            detail="Too many Q&A requests. Please retry later.",
            headers={"Retry-After": "60"},
        )

    acquired = qa_semaphore.acquire(blocking=False)
    if not acquired:
        raise HTTPException(
            status_code=503,
            detail="Repository Q&A is busy. Please retry shortly.",
        )

    try:
        return repository_service.ask(
            query=request.query.strip(),
            provider=active_llm_provider,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail="Repository analysis artifact is unavailable.",
        ) from error

    except ConnectionError as error:
        detail = (
            "Local LLM provider is unavailable."
            if llm_settings["provider"] == "ollama"
            else "Configured LLM provider is unavailable."
        )
        raise HTTPException(
            status_code=503,
            detail=detail,
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Repository Q&A failed unexpectedly.",
        ) from error

    finally:
        qa_semaphore.release()
