# RepoLens Frontend

Next.js/React/TypeScript frontend for RepoLens, an evidence-based codebase intelligence and architecture drift auditing product.

## Local development

```powershell
npm ci
npm run dev
```

Open `http://localhost:3000`. Configure `NEXT_PUBLIC_API_BASE_URL` when the FastAPI backend is not running at the local default.

## Production-style verification

```powershell
npm run lint
npx tsc --noEmit
npm run build
npm run start
```

The frontend talks only to the FastAPI API. It never connects directly to Ollama.
