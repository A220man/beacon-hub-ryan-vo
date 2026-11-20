# Changelog

## 1.7.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.6.1 — work-in-progress checkpoint

### Added
- OIDC/Keycloak authentication (auth-oidc feature)
- Backend token validation endpoint at `/api/v1/auth/callback`
- Frontend PKCE login flow with Keycloak integration
- Role-based access control (viewer/operator/admin) via auth guards
- Unauthenticated access rejection (401) on protected endpoints
- Frontend login/logout buttons in the navbar

### Changed
- Updated `frontend/src/App.tsx` to conditionally render based on auth state
- Updated `frontend/src/main.tsx` to wrap with `AuthProvider`
- Updated `backend/app/main.py` to include auth router
- Updated `PLAN.md` and `feature-plan.json` to track auth-oidc feature

### Known Issues
- PKCE code challenge generation uses Web Crypto API (client-side only)
- Token exchange between frontend and backend needs Keycloak client configuration
- Session management uses localStorage (consider HttpOnly cookies for production)

## 1.6.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.5.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.4.0 — work-in-progress checkpoint

### Fixed
- TypeScript errors in frontend test files: replaced `new Promise((resolve) => { resolve = r })` pattern with `Promise.withResolvers()` for proper type inference
- Frontend typecheck now passes without errors

### Verified
- All backend tests pass (60/60)
- All frontend tests pass (19/19)
- Frontend typecheck passes
- Frontend build passes

Partial code published for continued development. Known issues: STATUS.md.
## 1.3.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.2.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.1.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

### Added
- Added API test for 1MB request size limit on answer file validation endpoint

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

### Added
- FastAPI backend with `/api/v1/healthz` endpoint
- React + TypeScript + Vite frontend with health check display
- Docker Compose with PostgreSQL, Keycloak, backend, and frontend services
- Keycloak realm export with viewer/operator/admin roles
- Backend tests (pytest): health endpoint, config validation
- Frontend tests (vitest): health display, error states, feature list
- CI workflow (GitHub Actions): backend tests, frontend typecheck/build/tests, Docker builds
- Project configuration: pyproject.toml, portfolio.json, .env.example, .gitignore
- README with architecture diagram, API reference, AI/ML evaluation section
- MIT License with Ryan Vo copyright

### Security
- Non-root Docker users for backend and frontend
- HttpOnly/SameSite cookie considerations documented for future auth implementation
- Secret management via environment variables only
- Keycloak realm import for development only

### Infrastructure
- Healthchecks on all Docker services
- Bind ports to 127.0.0.1 for development
- Persistent PostgreSQL volume
- Nginx reverse proxy for frontend with API proxy to backend
