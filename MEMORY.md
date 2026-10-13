# PROJECT MEMORY & RUNNING BACKLOG

## [SYSTEM STATE]
### Architecture & Tech Stack
- **Backend:** FastAPI (Python 3.10), SQLAlchemy 2.0 (declarative), Alembic migrations, PostgreSQL (`psycopg2-binary`), Boto3 (S3/MinIO client).
  - **Entrypoint:** `code/backend/src/main.py`
  - **Configuration:** `code/backend/src/config.py` (reads `DATABASE_URL`, `JWT_SECRET_KEY`, `MINIO_*`, `ALLOWED_ORIGINS`, `DEBUG`). Automatically normalizes `postgres://` to `postgresql://` for Railway compatibility.
  - **Authentication:** JWT tokens stored in HttpOnly cookies (`samesite="none"` and `secure=True` in production; `samesite="lax"` and `secure=False` in development).
  - **Database Migrations:** Alembic (`alembic upgrade head`) automatically executed on container startup via `code/backend/Dockerfile`.
- **Frontend:** React 19, Vite 7, TailwindCSS v4, React Router 7, Axios (`code/frontend/src/services/api.js` with `withCredentials: true`), Leaflet.
  - **API Base URL:** Defaults to `/api` (same-origin reverse proxy).
  - **Local Development:** Vite dev server proxies `/api/*` to `http://localhost:8000/*` via `vite.config.js`.
  - **Production Hosting:** Multi-stage `code/frontend/Dockerfile` using `nginx:alpine` and `nginx.conf.template` with dynamic `$PORT` substitution, SPA fallback (`try_files $uri $uri/ /index.html`), gzip compression, security headers, and internal reverse proxy (`location /api/` -> `http://${BACKEND_HOST:-backend.railway.internal}:${BACKEND_PORT:-8000}/`).
- **Deployment & Infrastructure:**
  - **Local:** Docker Compose (`deployment/docker-compose.yml`) running PostgreSQL 15, MinIO, frontend dev server, and backend FastAPI server.
  - **Production (Railway):** Dual-service deployment with private internal backend. Frontend is the ONLY public-facing service. Backend communicates strictly across Railway's private network mesh (`backend.railway.internal:8000`).

### Operational Rules & Patterns
- **Rule Adherence:**
  - `clean-codebase-rule.md`: No dead code, no orphan files, clean dependencies.
  - `good-maintainabilty-rule.md`: SOLID principles, low coupling, dependency injection.
  - `api-response-rule.md`: Handle HTTP 204 No Content properly, strict async/await chains for data mutation & refetching.
  - `production.md`: Non-blocking async/await, defensive error handling, structured logging with `X-Trace-ID`.
  - `security-rules.md`: No JWT in localStorage, DOMPurify for user HTML, parameterized SQL queries, zero hardcoded secrets.
  - `test-rule.md`: AAA pattern, Normal/Edge/Extraordinary case coverage.
  - `memory-backlog.md`: Continuous memory & state management using `MEMORY.md` via the Read-Execute-Update loop.

---

## [RECENT CHANGES]
- **Cycle 4 (Backend Deployment Success):**
  - Backend service successfully booted on Railway: Alembic migrations applied against PostgreSQL, Uvicorn listening on port 8000, and healthcheck passing.
- **Cycle 5 (Internal Private Backend Architecture):**
  - Configured Nginx in `code/frontend/nginx.conf.template` to reverse proxy `/api/` to `http://${BACKEND_HOST:-backend.railway.internal}:${BACKEND_PORT:-8000}/` with `client_max_body_size 20M`.
  - Updated `code/frontend/Dockerfile` to interpolate `PORT`, `BACKEND_HOST`, and `BACKEND_PORT` via `envsubst`.
  - Updated `code/frontend/src/services/api.js` to default `API_URL` to `/api` (same-origin).
  - Updated `code/frontend/vite.config.js` to proxy `/api` to `http://localhost:8000` in local dev.
  - Updated `code/backend/src/main.py` cookie settings to `samesite="lax"` since the reverse proxy makes all requests same-origin.

---

## [ACTIVE BACKLOG]

### [BLOCKED]
- None currently.

### [IN PROGRESS]
- Deploying Frontend service on Railway:
  - Create service pointing to `code/frontend`.
  - Click "Generate Domain" on Frontend (only public URL needed).
  - No public domain needed on Backend (communicates via `backend.railway.internal`).

### [PENDING]
- **End-to-End Verification:** Verify frontend loads, routes to `/api`, authenticates, and retrieves data.
- **Production Storage Deployment:** Deploy MinIO template on Railway with persistent volume or configure S3 bucket credentials.
- **Database Seeding on Railway:** Run seed data ingestion in production if required.
- **Stashed Work Restoration:** Restore non-railway stashed files (`Reports/`, `Sprints/`) on `development` branch when ready.
