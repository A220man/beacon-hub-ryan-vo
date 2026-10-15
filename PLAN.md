# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

skeleton

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

### recipe-analyzer — Windows 11 recipe analyzer with ML failure prediction

Status: done

Acceptance:
- API endpoint to analyze a recipe JSON and return risk assessment
- ML model trained on synthetic failure patterns from issue data
- Frontend form to paste/upload recipe and view analysis
- Deterministic offline core works without LLM key

Implementation: `backend/app/models/recipe.py`, `backend/app/models/analysis.py`, `backend/app/services/predictor.py`, `backend/app/api/analysis.py`, `frontend/src/components/RecipeAnalyzer.tsx`, `frontend/src/components/RecipeAnalyzer.css`, `frontend/src/api/client.ts`

Tests: `backend/tests/test_predictor.py`, `backend/tests/test_analysis_api.py`

### component-advisor — AI-powered component removal advisor

Status: done

Acceptance:
- API endpoint recommending safe/unsafe components for a given Windows build
- Frontend wizard to select build version and get recommendations
- Explanations grounded in actual component dependency data

Implementation: `backend/app/models/recipe.py`, `backend/app/services/advisor.py`, `backend/app/api/analysis.py`, `frontend/src/components/ComponentAdvisor.tsx`, `frontend/src/components/ComponentAdvisor.css`, `frontend/src/api/client.ts`

Tests: `backend/tests/test_advisor.py`, `backend/tests/test_analysis_api.py`

### iso-validator — Unattended answer file validator

Status: done

Acceptance:
- API endpoint validating autounattend.xml for common errors
- Frontend upload/validation with detailed error reports
- Catches ProductKey, locale, and component mismatch issues

Implementation: `backend/app/models/answer_file.py`, `backend/app/services/answer_validator.py`, `backend/app/api/validation.py`, `frontend/src/components/AnswerFileValidator.tsx`, `frontend/src/components/AnswerFileValidator.css`, `frontend/src/api/client.ts`

Tests: `backend/tests/test_answer_validator.py`, `backend/tests/test_analysis_api.py`

### auth-oidc — OIDC/Keycloak authentication

Status: planned

Acceptance:
- Keycloak realm import provided
- Backend validates access tokens on all data endpoints
- Frontend PKCE login flow with callback
- Role-based access (viewer/operator/admin)
- Tests cover unauthenticated rejection and role denial

