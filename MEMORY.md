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

### Production Structure Map
- `code/backend/`: FastAPI application
  - `src/main.py`: API routes, middleware (CORS, trace ID, rate limiting), exception handlers.
  - `src/config.py`: Environment configuration and validation.
  - `src/database.py`: SQLAlchemy engine, session maker, base declarative model.
  - `src/models.py`: Database models (User, Source, Tag, Image, Object, image_tags).
  - `src/schemas.py`: Pydantic request and response schemas.
  - `src/auth.py`: Password hashing, JWT token creation, cookie auth dependencies.
  - `src/services/`: Service layer (ObjectService, s3_service).
  - `src/repositories/`: Repository layer (ObjectRepository).
  - `alembic/versions/`:
    - `d86f7k1a32b9_initial_schema.py`: Base table creation.
    - `e1a2b3c4d5e6_add_review_status_to_objects.py`: Adds `review_status` column and index to `objects`.
  - `Dockerfile`: Python 3.10-slim container, runs `alembic upgrade head` and `uvicorn --host '::'`.
- `code/frontend/`: React Vite frontend
  - `src/services/api.js`: Axios instance pointing to `/api`.
  - `src/contexts/AuthContext.jsx`: Auth state management.
  - `nginx.conf.template`: Production Nginx reverse proxy template routing `/api/*` to backend.
  - `Dockerfile`: Multi-stage build with Nginx and envsubst for dynamic PORT, BACKEND_HOST, and RESOLVER.

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
- **Cycle 7 (Fix 500 Internal Server Errors & Missing Schema Migration):**
  - Resolved missing database column: Added Alembic migration `e1a2b3c4d5e6_add_review_status_to_objects.py` to add `review_status` column and index to `objects` table (previously causing SQL crashes on `search` and `map` queries).
  - Fixed Nginx URI forwarding: Upgraded `nginx.conf.template` to use named capture `location ~ ^/api/?(?<path>.*)$` and explicit `proxy_pass $backend_target/$path$is_args$args;`, avoiding truncated paths with variable targets.
  - Added DNS resolver fallback: Injected `[fd12::10]` (Railway's internal IPv6 DNS) and `127.0.0.11` into Nginx resolver list.
  - Hardened backend: Added defensive `try/except SQLAlchemyError` handling and structured logging to `ObjectService.get_map_data` and `ObjectService.get_all_tags`. Made rate-limit middleware reverse-proxy safe with `X-Forwarded-For`.
  - Added unit test coverage for extraordinary database error handling.
- **Cycle 8 (Fix 502 Bad Gateway & Alembic String Literal Quotes):**
  - Resolved startup crash causing 502 Bad Gateway: In `e1a2b3c4d5e6_add_review_status_to_objects.py`, changed unquoted `server_default='accepted'` to explicit `server_default=sa.text("'accepted'")` and `op.execute(...)`. In PostgreSQL, raw unquoted string defaults evaluate to column identifiers, causing `column "accepted" does not exist` and preventing Uvicorn from starting.
  - Documented Railway port configuration requirements: Set `PORT=8000` on Backend service or `BACKEND_PORT=${{backend.PORT}}` on Frontend service to ensure internal port alignment.

---

## [ACTIVE BACKLOG]

### [BLOCKED]
- None currently.

### [IN PROGRESS]
- Verifying backend container boot with corrected Alembic migration and Railway port alignment.

### [PENDING]
- **Database Seeding on Railway:** Run seed data ingestion in production so artifacts appear on the search page.
- **Production Storage Deployment:** Deploy MinIO template on Railway with persistent volume or configure S3 bucket credentials.
- **Stashed Work Restoration:** Restore non-railway stashed files (`Reports/`, `Sprints/`) on `development` branch when ready.
