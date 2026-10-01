# RepoLens

**Evidence-Based Codebase Intelligence & Architecture Drift Auditor**

RepoLens analyzes a software repository and turns its structure into inspectable engineering evidence: repository overview, dependency graphs, architecture layers, risk signals, evidence retrieval, evidence-grounded Q&A, and architecture drift comparisons.

## Product architecture

```text
Repository artifacts
        ↓
Ingestion / parsing
        ↓
Deterministic analysis
 ┌──────┼───────────┐
 ↓      ↓           ↓
Deps  Architecture  Risks
 └──────┼───────────┘
        ↓
Evidence / retrieval
        ↓
Claim decomposition + verification
        ↓
Repository Q&A
        ↓
FastAPI backend
        ↓ HTTPS
Next.js dashboard
```

## Stack

- **Frontend:** Next.js 16, React 19, TypeScript, Tailwind CSS
- **Backend:** FastAPI, Python
- **Analysis:** deterministic repository/dependency/architecture/risk/drift pipeline
- **Q&A:** evidence retrieval + claim verification + server-side Ollama
- **Local model:** `qwen2.5-coder:7b`

## Requirements

- Python 3.11+
- Node.js 20+
- npm
- Ollama for Q&A
- `qwen2.5-coder:7b`

## 1. Backend setup

From the repository root:

```powershell
py -m pip install -r requirements.txt
py -m pytest -q
py -m uvicorn api.main:app --reload
```

Backend: `http://127.0.0.1:8000`

API docs: `http://127.0.0.1:8000/docs`

## 2. Ollama setup

Install/start Ollama, then verify the model:

```powershell
ollama list
ollama pull qwen2.5-coder:7b
```

The backend reads these server-side settings:

```text
LLM_PROVIDER=ollama
LLM_MODEL=qwen2.5-coder:7b
OLLAMA_BASE_URL=http://localhost:11434
LLM_TIMEOUT_SECONDS=120
```

Check model readiness:

```text
GET /health/llm
```

The browser never connects directly to Ollama.

## 3. Frontend setup

Open a second terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Frontend: `http://localhost:3000`

For a production-style local run:

```powershell
npm run lint
npx tsc --noEmit
npm run build
npm run start
```

## Environment configuration

Root `.env.example` contains server-side LLM/CORS settings. `frontend/.env.example` contains the browser-visible API origin.

For local development the defaults are sufficient. For deployment, set:

```text
NEXT_PUBLIC_API_BASE_URL=https://<your-api-origin>
CORS_ORIGINS=https://<your-frontend-origin>
```

Never put provider credentials in `NEXT_PUBLIC_*` variables.

## API surface

Core endpoints include:

- `GET /health`
- `GET /health/release`
- `GET /health/llm`
- `GET /api/repository/overview`
- `GET /api/repository/analysis`
- `GET /api/repository/drift`
- `POST /api/repository/ask`

The frontend routes are:

`/`, `/repository`, `/architecture`, `/dependencies`, `/risks`, `/security`, `/testing`, `/evidence`, `/qa`, `/drift`, `/reports`, `/evaluation`.

## Evidence and Q&A behavior

Repository content is treated as untrusted data. Retrieved evidence is used to support claims, and the Q&A pipeline can fail closed with `UNKNOWN` when the repository cannot verify an answer. Unsupported or unrelated questions must not be presented as repository facts.

## Demo artifacts

The release includes deterministic analysis artifacts for the `requests` repository so the dashboard can be demonstrated immediately. The current dashboard is not an anonymous arbitrary-repository upload service; that is a separate product capability.

## Drift behavior

Drift analysis compares compatible architecture snapshots. RepoLens does not invent a baseline or manufacture a "no drift" conclusion when a baseline is unavailable.

## Public deployment model

```text
Browser
   ↓ HTTPS
Next.js frontend
   ↓ HTTPS
FastAPI backend
   ↓
Deterministic analysis + evidence pipeline
   ↓
Ollama / server-side LLM
```

A public deployment cannot use the developer machine's `localhost:11434`. Ollama and the configured model must run on infrastructure reachable by the FastAPI service, or a server-side provider can be implemented behind the LLM provider boundary. No API key is required for the local Ollama path.

## Release verification

On Windows, run from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\verify_release.ps1
```

This performs backend tests/compile and a clean frontend install, lint, TypeScript check, and production build.

The final artifact also includes `FINAL_AUDIT.md` and `RELEASE_NOTES.md` describing the release scope and remaining runtime limitation.

## Production LLM configuration

RepoLens keeps Ollama as the default local provider. For a public deployment where the host machine does not run Ollama, configure the FastAPI server with Gemini:

```text
LLM_PROVIDER=gemini
LLM_MODEL=gemini-3.8-flash
GEMINI_API_KEY=<server-side-secret>
```

Keep `GEMINI_API_KEY` only in the backend host's environment/secrets. Never expose it through the Next.js frontend or commit it to Git.

For local development, omit these variables and RepoLens continues to use Ollama with `qwen2.5-coder:7b`.

Set `NEXT_PUBLIC_API_BASE_URL` on the frontend host to the deployed HTTPS FastAPI origin.
