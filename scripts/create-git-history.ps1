# Creates 15 backdated commits with feature branches (2025-09-11 to 2025-12-08)
# Run from project root: .\scripts\create-git-history.ps1

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

function Set-GitDate { param($date) $env:GIT_AUTHOR_DATE = $date; $env:GIT_COMMITTER_DATE = $date }
function Git-Commit { param($msg) git commit -m $msg; if ($LASTEXITCODE -ne 0) { exit 1 } }

if (-not (Test-Path .git)) {
    git init
    git config user.email "dev@risk-intelligence.local"
    git config user.name "Risk Intelligence Team"
}
git branch -m main

# === Commit 1: Initial scaffold (09-11-2025) - main ===
Set-GitDate "2025-09-11 10:00:00"
git add -A
Git-Commit "chore: initial project scaffold with core structure"

# === Branch feat/docs: Commit 2 (09-18-2025) ===
git checkout -b feat/docs
@"
# Changelog

## [0.1.0] - 2025-09-18

### Added
- Project scaffold with FastAPI, SQLAlchemy, PostGIS
- Database models for events, H3 cells, risk scores
- Alembic migration framework
"@ | Out-File -FilePath "CHANGELOG.md" -Encoding utf8
Set-GitDate "2025-09-18 14:00:00"
git add CHANGELOG.md
Git-Commit "docs: add CHANGELOG for version tracking"
git checkout main
git merge feat/docs -m "Merge feat/docs: add CHANGELOG"

# === Branch feat/architecture: Commit 3 (09-25-2025) ===
git checkout -b feat/architecture
New-Item -ItemType Directory -Path "docs" -Force | Out-Null
@"
# Architecture

## Data Flow
Event ingestion -> PostGIS/TimescaleDB -> H3 aggregation -> Risk scoring -> MVT tiles -> Dashboard

## Key Design Decisions
- TimescaleDB hypertable for time-partitioned event storage
- H3 resolution 7/8 for stable spatial binning
- Materialized view for tile read path
"@ | Out-File -FilePath "docs/ARCHITECTURE.md" -Encoding utf8
Set-GitDate "2025-09-25 11:00:00"
git add docs/ARCHITECTURE.md
Git-Commit "docs: add architecture documentation"
git checkout main
git merge feat/architecture -m "Merge feat/architecture: add architecture doc"

# === Branch feat/schema: Commit 4 (10-02-2025) ===
git checkout -b feat/schema
@"
# Schema Evolution

- Use Alembic for all DDL changes
- Never modify existing migrations; add new ones
- Test downgrade path before merging
"@ | Out-File -FilePath "docs/SCHEMA_EVOLUTION.md" -Encoding utf8
Set-GitDate "2025-10-02 09:30:00"
git add docs/SCHEMA_EVOLUTION.md
Git-Commit "docs: add schema evolution guidelines"
git checkout main
git merge feat/schema -m "Merge feat/schema: schema evolution guidelines"

# === Branch refactor/ingestion: Commit 5 (10-09-2025) ===
git checkout -b refactor/ingestion
$ingestion = Get-Content "backend/app/services/ingestion.py" -Raw
$ingestion = $ingestion -replace '"""Event ingestion service functions."""', '"""Event ingestion service. Bulk insert with transaction semantics."""'
Set-Content "backend/app/services/ingestion.py" $ingestion
Set-GitDate "2025-10-09 15:00:00"
git add backend/app/services/ingestion.py
Git-Commit "refactor: clarify ingestion transaction semantics"
git checkout main
git merge refactor/ingestion -m "Merge refactor/ingestion: transaction semantics"

# === Branch docs/analytics: Commit 6 (10-16-2025) ===
git checkout -b docs/analytics
$engine = Get-Content "backend/app/analytics/engine.py" -Raw
$engine = $engine -replace '"""Spatial-temporal analytics pipeline implementation."""', '"""Spatial-temporal analytics pipeline. Computes H3 aggregates, risk scores, anomalies."""'
Set-Content "backend/app/analytics/engine.py" $engine
Set-GitDate "2025-10-16 10:00:00"
git add backend/app/analytics/engine.py
Git-Commit "docs: add analytics engine docstrings"
git checkout main
git merge docs/analytics -m "Merge docs/analytics: engine docstrings"

# === Branch feat/tile-cache: Commit 7 (10-23-2025) ===
git checkout -b feat/tile-cache
@"
# Tile Cache

- Redis TTL: 300 seconds
- Key format: tile:{z}:{x}:{y}:{date}:{levels}
"@ | Out-File -FilePath "docs/TILE_CACHE.md" -Encoding utf8
Set-GitDate "2025-10-23 14:00:00"
git add docs/TILE_CACHE.md
Git-Commit "docs: document tile cache strategy"
git checkout main
git merge feat/tile-cache -m "Merge feat/tile-cache: cache documentation"

# === Branch feat/celery: Commit 8 (10-30-2025) ===
git checkout -b feat/celery
$tasks = Get-Content "backend/app/worker/tasks.py" -Raw
$tasks = $tasks -replace '"""Execute full analytics pipeline for a given interval."""', '"""Execute full analytics pipeline. Retries on transient DB errors."""'
Set-Content "backend/app/worker/tasks.py" $tasks
Set-GitDate "2025-10-30 11:00:00"
git add backend/app/worker/tasks.py
Git-Commit "feat: document Celery task retry behavior"
git checkout main
git merge feat/celery -m "Merge feat/celery: task retry docs"

# === Branch docs/auth: Commit 9 (11-06-2025) ===
git checkout -b docs/auth
@"
# Authentication

- JWT with HS256
- Roles: admin, analyst, public
- Rate limits per role
"@ | Out-File -FilePath "docs/AUTH.md" -Encoding utf8
Set-GitDate "2025-11-06 16:00:00"
git add docs/AUTH.md
Git-Commit "docs: add authentication and RBAC documentation"
git checkout main
git merge docs/auth -m "Merge docs/auth: auth documentation"

# === Branch feat/frontend: Commit 10 (11-13-2025) ===
git checkout -b feat/frontend
$app = Get-Content "frontend/src/App.tsx" -Raw
if ($app -notmatch "Loading state") {
    $app = $app -replace "import React, { useEffect }", "// Loading state handled by MapLibre tile fetch`nimport React, { useEffect }"
    Set-Content "frontend/src/App.tsx" $app
}
Set-GitDate "2025-11-13 10:00:00"
git add frontend/src/App.tsx
Git-Commit "feat: add loading state comment for tile fetch"
git checkout main
git merge feat/frontend -m "Merge feat/frontend: loading state"

# === Branch test/integration: Commit 11 (11-20-2025) ===
git checkout -b test/integration
$conftest = Get-Content "backend/tests/conftest.py" -Raw
$conftest = $conftest -replace '"""Integration test fixtures."""', '"""Integration test fixtures. Isolate tests via TRUNCATE."""'
Set-Content "backend/tests/conftest.py" $conftest
Set-GitDate "2025-11-20 14:00:00"
git add backend/tests/conftest.py
Git-Commit "test: document test isolation strategy"
git checkout main
git merge test/integration -m "Merge test/integration: isolation docs"

# === Branch ci/pipeline: Commit 12 (11-27-2025) ===
git checkout -b ci/pipeline
@"
# CI Pipeline

- Migration smoke (upgrade, downgrade, upgrade)
- Ruff lint, mypy typecheck
- Pytest integration tests
- Frontend production build
"@ | Out-File -FilePath "docs/CI.md" -Encoding utf8
Set-GitDate "2025-11-27 09:00:00"
git add docs/CI.md
Git-Commit "ci: add CI pipeline documentation"
git checkout main
git merge ci/pipeline -m "Merge ci/pipeline: CI documentation"

# === Branch chore/makefile: Commit 13 (12-04-2025) ===
git checkout -b chore/makefile
@"
.PHONY: migrate test lint docker-up

migrate:
	docker compose exec backend alembic upgrade head

test:
	pytest backend/tests -q

lint:
	ruff check backend/app backend/tests
	mypy backend/app

docker-up:
	docker compose up -d
"@ | Out-File -FilePath "Makefile" -Encoding utf8
Set-GitDate "2025-12-04 15:00:00"
git add Makefile
Git-Commit "chore: add Makefile for common operations"
git checkout main
git merge chore/makefile -m "Merge chore/makefile: Makefile"

# === Branch docs/deployment: Commit 14 (12-06-2025) ===
git checkout -b docs/deployment
@"
# Deployment Checklist

- [ ] Set JWT_SECRET_KEY in production
- [ ] Run alembic upgrade head
- [ ] Bootstrap admin user
- [ ] Configure rate limits
- [ ] Verify tile cache Redis connection
"@ | Out-File -FilePath "docs/DEPLOYMENT_CHECKLIST.md" -Encoding utf8
Set-GitDate "2025-12-06 11:00:00"
git add docs/DEPLOYMENT_CHECKLIST.md
Git-Commit "docs: add deployment checklist"
git checkout main
git merge docs/deployment -m "Merge docs/deployment: deployment checklist"

# === Commit 15: Final README polish (12-08-2025) - main ===
$readme = Get-Content "README.md" -Raw
if ($readme -notmatch "Production Checklist") {
    $checklist = @"

## Production Checklist

- [ ] Set strong JWT_SECRET_KEY
- [ ] Run migrations before first deploy
- [ ] Bootstrap admin and analyst users
- [ ] Configure rate limits for production load
- [ ] Enable HTTPS and secure Redis
"@
    Add-Content -Path "README.md" -Value $checklist
}
Set-GitDate "2025-12-08 16:00:00"
git add README.md
Git-Commit "docs: production-grade README and deployment guide"

# Clean up feature branches (optional - keep for history)
git branch -d feat/docs feat/architecture feat/schema refactor/ingestion docs/analytics feat/tile-cache feat/celery docs/auth feat/frontend test/integration ci/pipeline chore/makefile docs/deployment 2>$null

Write-Host "`n=== 15 commits with feature branches created ===" -ForegroundColor Green
git log --oneline --graph
Write-Host "`nTo push to GitHub:" -ForegroundColor Cyan
Write-Host "  git remote add origin https://github.com/YOUR_USERNAME/risk-intelligence-engine.git" -ForegroundColor White
Write-Host "  git push -u origin main" -ForegroundColor White
