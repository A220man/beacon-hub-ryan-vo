# Changelog

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-10-15

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