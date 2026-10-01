# RepoLens — 2026-09-30 Final Release

## Included
- Evidence-based repository overview and analysis
- Deterministic dependency and architecture graph
- Risk and security analysis surfaces
- Evidence/claim inspection
- Evidence-grounded repository Q&A through server-side Ollama + `qwen2.5-coder:7b`
- Architecture drift comparison from persisted snapshots
- Reports and deterministic evaluation surfaces
- Responsive navigation and architecture visualization

## Final hardening
- Architecture node labels are positioned tangentially so selected labels do not cover radial dependency edges or the repository core.
- Q&A concurrency/rate-limit environment configuration is resilient to malformed values.
- CORS is explicit and non-credentialed.
- Security headers and controlled backend error responses remain enabled.
- Historical audit/release-note clutter is excluded from the release tree.

## Data-integrity and reproducibility hardening
- Regenerated bundled `requests` analysis artifacts from the actual 103-file checkout so repository metadata, architecture snapshots, retrieval chunks, and Q&A evidence agree on the same source state.
- Canonicalized repository-relative evidence paths to Windows separators so regenerated evidence remains compatible with the release/API contract across tooling environments.
- Retained `frontend/package-lock.json` with Next.js 16.3.8 and `eslint-config-next` 16.3.8 for reproducible dependency installation.

## Deployment note
The current Q&A provider is Ollama. For a public deployment, run Ollama and the required model on infrastructure reachable by the FastAPI service, or implement another server-side provider behind the existing LLM provider interface. Do not expose Ollama directly to the browser.
