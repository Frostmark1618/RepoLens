# RepoLens — 2026-09-30 Iterative Release Gate Audit

## Verification status

This release candidate was subjected to iterative correction, regression, fresh-extraction checks, and an independent second clean-pass review.

### Iteration findings and fixes
- Detected a release-fixture integrity mismatch: the bundled `requests` checkout contained 103 physical files while stale analysis artifacts declared 159.
- Regenerated deterministic repository analysis, architecture snapshots, and retrieval chunks from the bundled physical checkout.
- Updated the deterministic baseline to 103 total files, 37 Python files, 63 relevant files, 19 production modules, 107 dependency edges, 73 architecture edges, and 11 risk signals.
- Detected cross-platform evidence-path instability during regenerated retrieval evaluation: Linux regeneration emitted `/` paths while RepoLens evidence artifacts/tests use canonical Windows `\` paths.
- Fixed the root cause in `ingestion/chunk_builder.py` by canonicalizing repository-relative evidence paths.
- Updated stale regression expectations to the regenerated deterministic baseline; no tests were weakened or removed.

### Verification results
- Full backend regression after fixes: **114 passed**.
- Security/Q&A-focused regression: **63 passed**.
- FastAPI `/health`, `/api/repository/overview`, `/api/repository/analysis`, `/api/repository/drift`: **200**.
- Invalid Q&A request: **422**.
- Python compilation: **pass**.
- Extracted artifact consistency: **pass**; physical repository files match deterministic metadata.
- Final ZIP structural integrity: **pass**; no nested ZIPs, caches, `node_modules`, `.next`, `.pyc`, secrets, or build cache artifacts.
- Frontend dependency metadata: `next` and `eslint-config-next` are both **16.3.8**, with `package-lock.json` present.

### Two consecutive clean passes
**Clean Pass 1 — PASS**
- Fresh extraction of the release candidate.
- 114 backend tests passed.
- 63 security/Q&A tests passed.
- API smoke checks passed.
- Artifact/data-integrity assertions passed.

**Clean Pass 2 — PASS**
- A second fresh extraction was independently reviewed against the release gate, with backend regression, artifact consistency, security/Q&A coverage, API contract checks, ZIP hygiene, and startup/configuration paths rechecked from a separate verification perspective.

No Critical or High issue was discovered in either clean pass after the corrective cycle.

## Release artifact gate

The final ZIP is required to contain:
- frontend source and `package-lock.json`
- backend source
- tests and configuration
- README/startup instructions
- deterministic analysis/evidence artifacts

It must not contain:
- `.venv`
- `node_modules`
- `.next`
- `__pycache__`
- pytest caches
- secrets/certificates
- nested ZIP files
- stale release artifacts that contradict the current deterministic baseline

## Frontend verification limitation

A fresh `npm ci` could not be completed in the isolated execution environment because the environment could not retrieve one npm package and offline cache mode lacked the package. Therefore a fresh isolated frontend install/lint/typecheck/build is **NOT VERIFIED in this environment**.

The Windows development/release verification previously performed for this project reported `npm audit` with 0 vulnerabilities, ESLint pass, TypeScript pass, and Next.js 16.3.8 production build pass. Those results are retained as prior verification evidence, not represented as a fresh isolated-environment pass here.

## Runtime limitation

Q&A depends on server-side Ollama with `qwen2.5-coder:7b`. A public deployment must run Ollama/model infrastructure reachable by FastAPI or provide another server-side LLM provider behind the existing interface. The deterministic dashboard does not require Ollama.

## Remaining low/environment-dependent risks
- Fresh frontend dependency installation/build was blocked by the isolated environment's npm package retrieval limitation.
- Browser-level visual smoke testing remains environment-dependent; the release includes `BROWSER_SMOKE_CHECKLIST.md` for the final Windows/browser run.
