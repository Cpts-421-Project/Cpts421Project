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
  - Updated `code/backend/src/main.py` cookie settings to `samesite="lax"`.
- **Cycle 6 (Internal Networking & Repository Sync):**
  - Identified Railway project was connected to user's personal GitHub fork (`asafked121/Cpts421Project`), synced remote branch with latest commits.
  - Configured Uvicorn in `code/backend/Dockerfile` to listen on `::` (IPv6 wildcard + dual-stack IPv4) to accept WireGuard mesh connections on Railway.
  - Added dynamic DNS resolver discovery (`awk '/nameserver/' /etc/resolv.conf`) and rewrite rules in `code/frontend/nginx.conf.template` to resolve internal Railway DNS and prevent stale IP timeouts.

---

## [ACTIVE BACKLOG]

### [BLOCKED]
- None currently.

### [IN PROGRESS]
- Verifying internal Railway reverse proxy connection between frontend and backend.

### [PENDING]
- **Database Seeding on Railway:** Run seed data ingestion in production so artifacts appear on the search page.
- **Production Storage Deployment:** Deploy MinIO template on Railway with persistent volume or configure S3 bucket credentials.
- **Stashed Work Restoration:** Restore non-railway stashed files (`Reports/`, `Sprints/`) on `development` branch when ready.
