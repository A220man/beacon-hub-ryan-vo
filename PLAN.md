# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

auth-oidc

## Roadmap

### skeleton — FastAPI/React skeleton with health check

Status: done

Acceptance:
- FastAPI backend starts and responds to /healthz
- React frontend builds and serves
- Docker compose brings up backend, frontend, and Keycloak
- Backend tests pass (pytest)
- Frontend typecheck and build pass
- CI workflow runs backend and frontend tests

Implementation: `backend/app/main.py`, `backend/app/core/config.py`, `backend/app/api/health.py`, `backend/requirements.txt`, `backend/Dockerfile`, `frontend/package.json`, `frontend/vite.config.ts`, `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/src/App.css`, `frontend/src/index.css`, `frontend/Dockerfile`, `frontend/nginx.conf`, `compose.yaml`, `keycloak/realm-export.json`, `.github/workflows/ci.yml`, `pyproject.toml`, `README.md`, `LICENSE`, `CHANGELOG.md`, `portfolio.json`, `.env.example`, `.gitignore`

Tests: `backend/tests/test_health.py`, `backend/tests/test_config.py`, `backend/tests/test_predictor.py`, `backend/tests/test_advisor.py`, `backend/tests/test_answer_validator.py`, `backend/tests/test_analysis_api.py`, `frontend/src/App.test.tsx`, `frontend/src/test-setup.ts`, `frontend/vitest.config.ts`

### auth-oidc — OIDC/Keycloak authentication

Status: in_progress

Acceptance:
- Keycloak realm import provided
- Backend validates access tokens on all data endpoints
- Frontend PKCE login flow with callback
- Role-based access (viewer/operator/admin)
- Tests cover unauthenticated rejection and role denial

Implementation: `backend/app/api/auth.py`, `backend/app/main.py`, `frontend/src/auth/pkce.ts`, `frontend/src/auth/auth-context.tsx`, `frontend/src/auth/callback.tsx`, `frontend/src/main.tsx`, `frontend/src/App.tsx`

Tests: `backend/tests/test_auth.py`

