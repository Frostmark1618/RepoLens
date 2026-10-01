$ErrorActionPreference = "Stop"

Write-Host "RepoLens release verification" -ForegroundColor Cyan
Write-Host "Root: $PWD"

Write-Host "`n[1/6] Backend tests" -ForegroundColor Yellow
py -m pytest -q

Write-Host "`n[2/6] Backend compile" -ForegroundColor Yellow
py -m compileall -q .

Write-Host "`n[3/6] Frontend clean install" -ForegroundColor Yellow
Push-Location frontend
try {
    npm ci

    Write-Host "`n[4/6] Frontend lint" -ForegroundColor Yellow
    npm run lint

    Write-Host "`n[5/6] Frontend TypeScript" -ForegroundColor Yellow
    npx tsc --noEmit

    Write-Host "`n[6/6] Frontend production build" -ForegroundColor Yellow
    npm run build
} finally {
    Pop-Location
}

Write-Host "`nRelease verification commands completed successfully." -ForegroundColor Green
Write-Host "Next: run the browser smoke checklist from BROWSER_SMOKE_CHECKLIST.md" -ForegroundColor Cyan
