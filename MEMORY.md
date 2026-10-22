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
  - `src/main.py`: API routes, middleware (CORS, trace ID, bot defense, rate limiting), exception handlers.
  - `src/bot_defense.py`: Anti-bot engine (BotJail, LoginRateLimiter, scanner User-Agent detection, honeypot traps, client IP extraction).
  - `src/config.py`: Environment configuration and validation.
  - `src/database.py`: SQLAlchemy engine, session maker, base declarative model.
  - `src/models.py`: Database models (User, Source, Tag, Image, Object, image_tags).
  - `src/schemas.py`: Pydantic request and response schemas (with anti-bot honeypot fields on UserLogin).
  - `src/auth.py`: Password hashing, JWT token creation, cookie auth dependencies.
  - `src/url_validator.py`: Core URL validation and domain allowlists for SSRF prevention.
  - `src/services/`: Service layer (ObjectService, s3_service).
  - `src/repositories/`: Repository layer (ObjectRepository).
  - `datacollection/`: Data ingestion pipeline (British Museum, Met API scrapers, S3/MinIO upload utils, URL validation).
  - `alembic/versions/`:
    - `d86f7k1a32b9_initial_schema.py`: Base table creation.
    - `e1a2b3c4d5e6_add_review_status_to_objects.py`: Adds `review_status` column and index to `objects`.
  - `Dockerfile`: Python 3.10-slim container, runs `alembic upgrade head && python seed_db.py && uvicorn --host '::'`.
  - `seed_db.py`: Database seeder and image migration script with idempotent SQL execution, bucket migration, and admin account provisioning.
  - `data/filtered_small.sql`: Seed dataset bundled directly within the backend build context (expanded with 27 Met + 21 British Museum curated ancient worker artifacts = 60 total artifacts).
  - `data/met_ancient_workers.sql`: Standalone idempotent SQL seed script for Met Museum ancient workers (27 artifacts).
  - `data/met_ancient_workers.json`: Curated dataset of 27 ancient worker artifacts from The Metropolitan Museum of Art.
  - `data/bm_ancient_workers.sql`: Standalone idempotent SQL seed script for British Museum ancient workers (21 artifacts).
  - `data/bm_ancient_workers.json`: Curated dataset of 21 ancient worker artifacts from The British Museum with rich academic descriptions and metadata.
  - `data/images/`: Seed artifact image bundle (60 total images) for offline and deploy-time bucket population.
  - `tests/`: `test_seed_db.py`, `test_main.py`, `test_ingestion.py`, `test_s3_service.py`, `test_bot_defense.py`.
- `code/frontend/`: React Vite frontend
  - `public/robots.txt`: Crawler policy disallowing sensitive routes, crawl delays, and AI scraper blocks.
  - `src/services/api.js`: Axios instance pointing to `/api`.
  - `src/contexts/AuthContext.jsx`: Auth state management with honeypot parameter support.
  - `src/components/Layout.jsx`: Root layout with invisible honeypot trap link.
  - `src/pages/LoginPage.jsx`: Login view with hidden honeypot field.
  - `nginx.conf.template`: Production Nginx reverse proxy template routing `/api/*` to backend with scanner bot blocking, rate limiting zones, and exploit probe rejection.
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
- **Cycle 9 (Original Team Repo Sync & PR #29 Merged):**
  - Railway switched to team repository (`Cpts-421-Project/Cpts421Project`).
  - Created Pull Request [#29](https://github.com/Cpts-421-Project/Cpts421Project/pull/29), passed all 4 CI checks (Structure, Backend CI, Frontend & Backend Docker build), and merged it into `origin/main`.
  - Synced local `main` and `personal/main` with `origin/main` at commit `a0410de`. Railway now deploys the fixes from the primary team repository.
- **Cycle 10 (Production Verification Success):**
  - End-to-end functionality verified in production on Railway.
  - Frontend Nginx successfully proxying API calls (`/api/objects/search`, `/api/tags`, `/api/objects/map`) over the private WireGuard mesh to `backend.railway.internal:8000`.
  - Database migrations applied cleanly in PostgreSQL and application responding with 200 OK.
- **Cycle 11 (Railway S3 / Storage Bucket Support):**
  - Updated `code/backend/src/config.py` to seamlessly accept standard S3/AWS/Tigris environment variables (`AWS_ENDPOINT_URL`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `BUCKET_NAME`) in addition to `MINIO_*`.
  - Configured Boto3 S3 client in `code/backend/src/services/s3_service.py` with path-style addressing (`s3={'addressing_style': 'path'}`) and region support.
  - Merged via PR [#31](https://github.com/Cpts-421-Project/Cpts421Project/pull/31) into `origin/main`.
- **Cycle 12 (Railway Storage Bucket Variables Configured):**
  - Verified user's Backend service configuration referencing the `Images` bucket:
    - `MINIO_ACCESS_KEY` = `${{Images.ACCESS_KEY_ID}}`
    - `MINIO_BUCKET` = `${{Images.RAILWAY_BUCKET_NAME}}`
    - `MINIO_ENDPOINT` = `${{Images.ENDPOINT}}`
    - `MINIO_PUBLIC_URL` = `${{Images.ENDPOINT}}`
    - `MINIO_SECRET_KEY` = `${{Images.SECRET_ACCESS_KEY}}`
  - All variables mapped and aligned with `Config` and `s3_service.py`.
- **Cycle 13 (Automated Production Database Seeding):**
  - Created standalone idempotent seeder script [seed_db.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/seed_db.py) supporting local, Docker Compose, and remote Railway environments.
  - Bundled seed dataset [filtered_small.sql](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/data/filtered_small.sql) inside `code/backend/data/` for container build context.
  - Updated [Dockerfile](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/Dockerfile) startup command to execute `seed_db.py` directly after Alembic migrations, automatically seeding Railway's PostgreSQL database securely over the internal network on deploy.
  - Added unit test suite [test_seed_db.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/tests/test_seed_db.py) following AAA pattern and testing Normal, Edge, and Extraordinary cases.
  - Added explicit `bcrypt` dependency in [requirements.txt](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/backend/requirements.txt).
  - Pushed to `staging` at commit `3217cf9`; verified `/api/tags` and `/api/objects/search` returning seeded artifacts in production.
- **Cycle 14 (Flexible Case-Insensitive & Email Login Authentication):**
  - Upgraded `/auth/login` endpoint in [main.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/backend/src/main.py) to match users by either `username` or `email` case-insensitively using `func.lower()`.
  - Updated [LoginPage.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/frontend/src/pages/LoginPage.jsx) label to "Username or Email" and removed placeholder pretext.
  - Updated [AuthContext.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/frontend/src/contexts/AuthContext.jsx) to store canonical username returned from backend.
  - Added unit test suite `TestAuthLogin` in [test_main.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/backend/tests/test_main.py) testing exact username, lowercase username, email login, wrong password, and non-existent user.
- **Cycle 15 (Codebase Cleanup):**
  - Deleted 8 orphaned one-off scripts from `code/backend/`: `api_test.py`, `clean_db.py`, `sql_clean.py`, `sql_test.py`, `test_db.py`, `migrate_review_mode.py`, `migrate_users.py` (contained hardcoded plaintext passwords), `retro_cache.py`.
  - Removed `import_log.txt` from git tracking (`git rm --cached`) and added to `.gitignore`.
  - Deleted empty placeholder directories and files: `code/Filter/`, `code/scripts/` (3 empty shell scripts), `data/processed/`, `data/raw/`.
  - Deleted orphaned `deployment/dummy_data/` directory (old dummy seeds + PNGs, unreferenced by any config).
  - Cleaned `.gitignore`: removed rambling internal-debate comments, added entries for `*.log`, `import_log.txt`, `.pytest_cache/`.
- **Cycle 16 (Pull Request #38 Merged into Main):**
  - Synced `staging` branch with latest remote `main` commits and opened Pull Request [#38](https://github.com/Cpts-421-Project/Cpts421Project/pull/38).
  - All 8 CI checks passed (`Structure Check`, `Frontend CI`, `Backend CI`, `Docker Builds`, Railway).
  - Successfully merged PR [#38](https://github.com/Cpts-421-Project/Cpts421Project/pull/38) into `main` at commit `5540aa3`.
  - Synced local `main` and `personal/main` with `origin/main`. Changes including automated seeder, case-insensitive auth, login UI polish, and codebase cleanup are now live on `main`.
- **Cycle 17 (Search Bar & Tag Filtering End-to-End Implementation):**
  - Backend API & Service:
    - Updated `/objects/search` endpoint in [main.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/backend/src/main.py) to accept `search`, `q`, `tags`, `tag`, and `tag_mode` parameters.
    - Added multi-field text search in [object_repository.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/backend/src/repositories/object_repository.py) covering `object_type`, `description`, `material`, `findspot`, `inventory_number`, and tag names via `ilike` and `or_`.
    - Added tag filtering matching associated tags with case-insensitivity and support for `any` (OR) and `all` (AND) modes.
    - Eager-loaded `Image.tags` with `joinedload` and invoked `.all()` to eliminate N+1 queries.
    - Added `tags: List[str]` to `ObjectDetailResponse` in [schemas.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/backend/src/schemas.py) and enriched dicts in [object_service.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/backend/src/services/object_service.py).
    - Added comprehensive unit tests in [test_main.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/backend/tests/test_main.py) under `TestSearchAndTags`. All 40 backend tests and 10 frontend tests passing.
  - Frontend UI & State:
    - Updated [useArtifacts.js](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/frontend/src/hooks/useArtifacts.js) to pass `search` and `tags` query parameters.
    - Configured `paramsSerializer: { indexes: null }` in [api.js](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/frontend/src/services/api.js).
    - Enhanced [SearchPage.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/frontend/src/pages/SearchPage.jsx) with URL query synchronization (`useSearchParams`), clearable search input with icon, active filter chips with one-click removal, and improved empty state.
    - Enhanced [FilterSidebar.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/frontend/src/components/FilterSidebar.jsx) with filter reset, active tag counter, tag search filter, and parent state synchronization.
    - Added tag chips rendering on [ArtifactGrid.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/frontend/src/components/ArtifactGrid.jsx) and [ObjectPage.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/frontend/src/pages/ObjectPage.jsx).
    - Verified production build compiles cleanly (`npm run build`).

- **Cycle 18 (Pull Request #39 Merged into Main with Search and Tags):**
  - All 8 CI checks passed on PR [#39](https://github.com/Cpts-421-Project/Cpts421Project/pull/39) (`Structure Check`, `Frontend CI 18.x`, `Frontend CI 20.x`, `Production CI/CD backend-test`, `Production CI/CD frontend-test`, `Backend CI`, `Railway Backend`, `Railway Frontend`).
  - Successfully merged PR [#39](https://github.com/Cpts-421-Project/Cpts421Project/pull/39) into `main` at commit `70003a2`.
  - Synced local `main`, `staging`, `origin/main`, `origin/staging`, `personal/main`, and `personal/staging`.
  - Verified 40/40 backend tests and 10/10 frontend tests passing.
  - Search bar and tag filtering are now deployed and live on both `staging` and `main`.

- **Cycle 19 (Enforce Bucket Storage For All Photos & Automated Seed Migration):**
  - Unified Storage Architecture & Security:
    - Updated [s3_service.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/backend/src/services/s3_service.py) with `is_bucket_url`, `validate_magic_bytes` (JPEG, PNG, WebP, GIF), `upload_bytes_to_minio`, `download_and_store_image` (with SSRF protection, 10MB streaming size limit, and MIME magic-byte verification), and `ensure_stored_in_bucket`.
    - Extracted core SSRF domain allowlists and validation into [url_validator.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/backend/src/url_validator.py), eliminating circular dependencies and DRY violations between `src` and `datacollection`.
    - Updated [cache_utils.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/backend/datacollection/cache_utils.py) and [s3_utils.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/backend/datacollection/s3_utils.py) to delegate directly to `s3_service` and `config`.
  - Auto-Bucket Pipeline in API & Services:
    - Updated [object_service.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/backend/src/services/object_service.py) `create_object` and `update_object` to automatically route any external image URLs through `ensure_stored_in_bucket`, guaranteeing that photos added or updated on artifacts are always stored in our own storage bucket rather than external servers.
  - Pre-Downloaded Seed Assets & Automated Seeder Migration:
    - Downloaded and bundled all 12 seed images into `code/backend/data/images/` and `data/reduced_dataset/images/` (`met_<inventory_number>.jpg`).
    - Enhanced [seed_db.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/backend/seed_db.py) with `migrate_external_images_to_bucket()`, automatically migrating any external images in PostgreSQL to our bucket upon deployment, utilizing local bundled image assets first (zero network overhead/offline safe) and streaming external downloads as fallback.
    - Updated [filtered_small.sql](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/backend/data/filtered_small.sql) to check `NOT EXISTS (SELECT 1 FROM images i WHERE i.object_id = o.id)` so re-seeding on already-migrated databases remains strictly idempotent.
  - Test Suite & Quality Assurance:
    - Added [test_s3_service.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/backend/tests/test_s3_service.py) with 20 unit tests covering Normal, Edge, and Extraordinary scenarios (SSRF domain blocking, DoS payload size limits, magic bytes, S3 errors, and ObjectService auto-caching).
    - Added unit tests in [test_seed_db.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/backend/tests/test_seed_db.py) testing image migration to bucket with local assets, skipping already-cached images, and graceful degradation when credentials are missing.
- **Cycle 20 (Direct Internal Bucket Proxy & External Met URL Sanitization):**
  - **Root Cause Identified:**
    - Seed SQL files (`code/backend/data/filtered_small.sql` and `data/reduced_dataset/filtered_small.sql`) retained 12 hardcoded `https://collectionapi.metmuseum.org/api/collection/v1/iiif/...` URLs.
    - Existing Postgres databases already held these external URLs, causing `/objects/search` and `/objects/{id}` to send external Met URLs to the frontend browser `<img>` tags.
  - **Direct Internal Bucket Proxy & Streaming (`main.py`):**
    - Added `@app.get("/images/{key:path}")` and `@app.get("/api/images/{key:path}")` endpoints in [main.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/backend/src/main.py).
    - Hardened with path traversal protection (`..`, `\`, leading `/`, `~` rejection).
    - Streams directly from private S3/Tigris/MinIO bucket using backend credentials, eliminating browser CORS restrictions and private bucket permission failures.
    - Implemented automatic fallback to bundled seed image assets (`code/backend/data/images/met_*.jpg`) with lazy auto-upload to the S3 bucket.
    - Added HTTP caching headers (`Cache-Control: public, max-age=86400`) and security headers (`X-Content-Type-Options: nosniff`).
  - **Database Migration & Seed Sanitization:**
    - Updated all 12 seed records in [filtered_small.sql](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/backend/data/filtered_small.sql) and [data/reduced_dataset/filtered_small.sql](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/data/reduced_dataset/filtered_small.sql) to `/api/images/met_<inventory_number>.jpg`.
    - Added `update_legacy_image_urls()` to [seed_db.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/backend/seed_db.py), automatically executing on deployment before server startup to rewrite any existing rows in PostgreSQL from Met URLs to `/api/images/met_<inv>.jpg`.
  - **Multi-Layer Defensive Normalization:**
    - In [object_service.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/backend/src/services/object_service.py) (`_enrich_object_dict`), added `_normalize_image_url` to guarantee no external Met URLs can be returned from API queries.
    - In [schemas.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/backend/src/schemas.py), added a Pydantic `field_validator` on `ImageResponse.file_url` to normalize legacy Met URLs before API serialization.
    - In [config.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/backend/src/config.py), added Railway aliases (`ENDPOINT`, `ACCESS_KEY_ID`, `SECRET_ACCESS_KEY`, `RAILWAY_BUCKET_NAME`) and defaulted `MINIO_PUBLIC_URL` to `/api/images`.
  - **Quality Assurance & Verification:**
    - Added comprehensive unit tests in [test_main.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/backend/tests/test_main.py) (`TestServeImage`, `TestLegacyUrlNormalization`) and [test_seed_db.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/backend/tests/test_seed_db.py) covering image streaming, S3 mocking, path traversal prevention, and legacy URL normalization.
    - Total tests: 101/101 backend unit tests passing, 10/10 frontend Vitest tests passing.

- **Cycle 21 (Comprehensive Security Audit Remediation & Hardening):**
  - **Secret Elimination & Dynamic Admin Provisioning:**
    - In [seed_db.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/backend/seed_db.py): Removed hardcoded plaintext admin passwords from VCS. Passwords now load dynamically via environment variables (`ADMIN_HALLIE_PASSWORD`, `ADMIN_ASAF_PASSWORD`, `ADMIN_PASSWORD_1`, `ADMIN_PASSWORD_2`) with secure cryptographic generation (`secrets.token_urlsafe(18)`) in production or dev fallbacks in testing.
    - Updated test fixtures in [test_main.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/backend/tests/test_main.py) to use isolated test passwords.
  - **Rate Limiting Memory Exhaustion & IP Spoofing Mitigation:**
    - In [main.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/backend/src/main.py): Resolved client IP via `X-Real-IP` (set directly by Nginx from `$remote_addr`), mitigating `X-Forwarded-For` client spoofing.
    - Implemented store pruning for expired entries and capped memory to `MAX_RATE_LIMIT_STORE = 10000` to prevent memory exhaustion DoS.
  - **Input Validation, Schema Hardening & Mass Assignment Protection:**
    - In [schemas.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/backend/src/schemas.py): Added `Literal["accepted", "rejected", "pending"]` validation to `ReviewUpdate`.
    - Removed `review_status` from `ObjectBase`, preventing clients from setting `review_status` upon creation or update. Retained on `ObjectDetailResponse`.
    - In [object_repository.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/backend/src/repositories/object_repository.py): Enforced `UPDATABLE_OBJECT_FIELDS` whitelist against mass assignment. Replaced mutable list default arguments with `Optional[List[dict]] = None`.
    - In [object_service.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/backend/src/services/object_service.py): Fixed `update_object` to preserve existing images when updating metadata without image payloads.
  - **Safe Storage Uploads & Strict HTTPS SSRF Defense:**
    - In [s3_service.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/backend/src/services/s3_service.py): Streamed file uploads in 64 KB chunks with size accumulation and early abort against memory DoS. Forced S3 `ContentType` and filename extension to magic-byte detected MIME (`detected_mime`).
    - In [url_validator.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/backend/src/url_validator.py): Restricted `ALLOWED_SCHEMES = frozenset({"https"})` to block HTTP downgrade SSRF.
  - **Defense-in-Depth & Hygiene:**
    - In [main.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/backend/src/main.py): Constant-time password verification with decoy hash (`DUMMY_PASSWORD_HASH`) to prevent timing side-channels on user enumeration. Masked identifiers in auth logs.
    - Hardened path traversal protection in `serve_image` using `PurePosixPath` and null byte detection.
    - Explicitly restricted CORS methods and headers.
    - Added `path="/"` and `httponly=True` to `delete_cookie`.
    - Replaced deprecated `datetime.utcnow()` with `datetime.now(timezone.utc)` in [auth.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/backend/src/auth.py) and [logger.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/backend/src/logger.py).
    - In [exceptions.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/backend/src/exceptions.py): Fixed `EntityNotFoundError` boundary check for `entity_id = 0`.
    - In [nginx.conf.template](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/frontend/nginx.conf.template): Injected `Content-Security-Policy` and `Strict-Transport-Security` headers.
  - **Quality Assurance & Verification:**
    - Added unit test suite `TestSecurityAuditRemediations` in [test_main.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/backend/tests/test_main.py) covering review status validation, creation defense, path traversal, null bytes, entity IDs, and logout cookies.
    - Total tests: 108/108 backend tests passing with 0 warnings (72.7s), 10/10 frontend Vitest tests passing, frontend Vite build clean.

- **Cycle 22 (System Security Rules Upgrade):**
  - **Comprehensive Rule Hardening:** Updated [.agents/rules/security-rules.md](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/.agents/rules/security-rules.md) with 9 dedicated architectural sections and a pre-commit checklist.
  - Codified permanent developer constraints for: zero plaintext credentials in seeders/VCS, bounded in-memory rate limiting with cache eviction, reverse proxy `X-Real-IP` resolution, streaming chunked file uploads, magic-byte MIME/extension enforcement, mass assignment attribute whitelisting, strict `Literal` status validation, timing attack constant-time decoys, `PurePosixPath` traversal blocking, and log masking.

- **Cycle 23 (Pull Request #42 Merged into Main with Security Updates):**
  - **Pull Request Creation & CI Pipeline:** Opened Pull Request [#42](https://github.com/Cpts-421-Project/Cpts421Project/pull/42) from `staging` into `main`.
  - **CI & Deployment Verification:** All 8 CI and deployment checks passed cleanly (Structure Check, Frontend CI Node 18.x & 20.x, Production CI/CD backend & frontend tests, Backend CI unit tests, Railway frontend & backend builds).
  - **Production Merge:** Successfully merged PR [#42](https://github.com/Cpts-421-Project/Cpts421Project/pull/42) into `origin/main` at commit `9f07222`.
  - **Branch Synchronization:** Synced local `main`, `origin/main`, `staging`, `origin/staging`, `personal/main`, and `personal/staging`.

- **Cycle 24 (Comprehensive Multi-Layer Anti-Bot & Abuse Defense Implementation):**
  - **Architecture & Threat Vector Defense:**
    - Addressed automated vulnerability scanners, brute-force credential stuffing, crawler/scraper denial of service, and bot form spam across Nginx, backend middleware, frontend forms, and crawler policies.
  - **Backend Bot Defense Engine (`bot_defense.py`):**
    - Implemented [bot_defense.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/backend/src/bot_defense.py) with `BotJail` (temporary IP banning with 1-hour ban duration, bounded memory store of 5,000 IPs, and TTL cleanup eviction to prevent memory exhaustion DoS).
    - Implemented `LoginRateLimiter` with strict sliding-window request throttling (10 requests/60s per IP) and consecutive failure tracking (locks out IP and target username after 5 consecutive failed logins for 15 minutes).
    - Added regex signature matching (`BAD_BOT_PATTERN`) detecting known security scanners and exploit tools (`sqlmap`, `nikto`, `acunetix`, `dirbuster`, `gobuster`, `nuclei`, `wpscan`, `masscan`, `zgrab`, `censys`, `shodan`, `nmap`).
    - Added `extract_client_ip` prioritizing reverse proxy `X-Real-IP` set by Nginx from `$remote_addr`.
    - Added `reset_bot_defense_state` for deterministic test isolation.
  - **FastAPI API & Middleware Integration (`main.py` & `schemas.py`):**
    - Added `bot_defense_middleware` executing before route handlers: immediately rejects banned IPs with 403, detects malicious scanner User-Agents and jails them, blocks common exploit probes (`/.env`, `/.git`, `/wp-`, `/xmlrpc.php`), and enforces non-empty User-Agents on mutating endpoints (`POST`, `PUT`, `PATCH`, `DELETE`).
    - Added honeypot endpoints `@app.get("/bot-trap")`, `/api/bot-trap`, `@app.post("/bot-trap")`, `/api/bot-trap`: any crawler accessing these routes is automatically jailed with 403.
    - Updated `/auth/login` endpoint with anti-bot honeypot field detection (`honeypot` and `website` in [schemas.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/backend/src/schemas.py)): automated form bots auto-filling the field are immediately rejected with 400 and jailed.
    - Integrated `login_rate_limiter` into `/auth/login` to prevent brute force and credential stuffing, preserving constant-time decoy password hashing and identifier masking.
    - Added `/robots.txt` fallback endpoint directing crawlers and disallowing AI scrapers.
  - **Frontend Honeypot & Crawler Governance:**
    - Created [robots.txt](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/frontend/public/robots.txt) disallowing `/api/`, `/auth/`, `/bot-trap`, `/upload-images`, enforcing `Crawl-delay: 5`, and explicitly blocking aggressive AI scrapers (`GPTBot`, `CCBot`, `Bytespider`, `ClaudeBot`, `Anthropic-AI`, `Scrapy`, etc.).
    - Added invisible honeypot trap link in [Layout.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/frontend/src/components/Layout.jsx) to trap automated web crawlers.
    - Added hidden honeypot field (`website`) in [LoginPage.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/frontend/src/pages/LoginPage.jsx) and updated [AuthContext.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/frontend/src/contexts/AuthContext.jsx) to pass honeypot state.
  - **Nginx Edge Layer Hardening (`nginx.conf.template`):**
    - Configured User-Agent bad bot map (`$bad_bot`) returning 403 Forbidden.
    - Configured rate limiting zones (`limit_req_zone` for API at 30r/s and login at 5r/m with 429 status).
    - Blocked exploit probe paths (`.env`, `.git`, `.php`, `.asp`, `.jsp`, etc.) returning 444 before reaching upstream.
    - Dedicated `location = /api/auth/login` rate limiting block.
  - **Quality Assurance & Verification:**
    - Created [test_bot_defense.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/backend/tests/test_bot_defense.py) covering Normal, Edge, and Extraordinary cases (AAA pattern).
    - Updated [test_main.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/backend/tests/test_main.py) setup fixture to call `reset_bot_defense_state()`.

---

- **Cycle 25 (Ancient Workers Dataset Discovery & Met Museum Ingestion):**
  - **Domain Research & Met Collection Exploration:**
    - Researched and curated a high-resolution, public-domain dataset of 27 authentic artifacts depicting ancient workers, craftspeople, trades, and agricultural labor from The Metropolitan Museum of Art across Egyptian, Greek, Roman, and Mesopotamian civilizations.
    - **Ancient Egypt:** Meketre Middle Kingdom models (granary with scribes, bakery and brewery, cattle stable, oxen plowing, slaughterhouse butchery, paddling and rowing crews, kitchen tender cooks, estate figure), New Kingdom workshop facsimiles from the Tomb of Rekhmire (brickmakers mixing mud and water, colossus/sphinx sculptors, joiners/carpenters, bronze smelters and casting molds, goldsmiths), Tomb of Nebamun & Ipuky (jewelers, goldsmiths, sculptors), Tomb of Sennedjem (agricultural plowing, sowing, and reaping in Fields of Iaru), and Henettawy agricultural worker shabti.
    - **Ancient Greece:** Attic black-figure Amasis Painter lekythos (women spinning wool, weaving at vertical warp-weighted loom, weighing fleece), Hellenistic master artisan bronze with silver eyes and wax tablets, Hellenistic foundry youth bronze, and Archaic hydria (women drawing water at fountain house).
    - **Ancient Rome:** 2nd-century marble commercial transport relief (merchant receiving sealed amphorae cargo from dock porter), and Cypriot terracotta mold-made relief lamps depicting enslaved workers preparing food and carrying heavy cargo on shoulder poles.
    - **Ancient Mesopotamia (Ur III / Neo-Sumerian):** Copper foundation figures of King Ur-Namma and King Shulgi assuming the role of master builders carrying brick baskets of mortar on their heads.
  - **Data Bundling & Seed Pipeline Integration:**
    - Created [met_ancient_workers.json](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/backend/data/met_ancient_workers.json) containing structured JSON records with dimensions, dates, findspots, materials, tags, and detailed academic descriptions.
    - Created standalone idempotent seed file [met_ancient_workers.sql](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/backend/data/met_ancient_workers.sql).
    - Merged all 27 records into [filtered_small.sql](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/backend/data/filtered_small.sql), expanding the seed dataset from 12 to 39 artifacts with zero external URL dependencies.
  - **Pull Request #43 Merged into Main:**
    - Opened PR [#43](https://github.com/Cpts-421-Project/Cpts421Project/pull/43) from `staging` into `main`.
    - Passed all 8 CI checks and deployment verifications (`Structure Check`, `Frontend CI 18.x`, `Frontend CI 20.x`, `Production CI/CD frontend-test`, `Backend CI test`, `Production CI/CD backend-test`, `Railway Frontend`, `Railway Backend`).
    - Successfully merged PR [#43](https://github.com/Cpts-421-Project/Cpts421Project/pull/43) into `origin/main` at commit `541c2d3`.
    - Synced local `main`, `origin/main`, `personal/main`, `staging`, `origin/staging`, and `personal/staging`.
    - Railway automatically builds and deploys the expanded dataset into live PostgreSQL and Tigris/S3 storage.

---

- **Cycle 26 (Ancient Workers Dataset Discovery & British Museum Ingestion):**
  - **Domain Research & British Museum Collection Exploration:**
    - Researched and curated a high-resolution, public-domain dataset of 21 authentic artifacts depicting ancient workers, craftspeople, trades, and agricultural labor from The British Museum across Egyptian, Greek, Roman, and Mesopotamian civilizations.
    - **Ancient Egypt:** Tomb-chapel of Nebamun wall paintings (Inspecting cattle and herdsmen, counting geese and poultry, assessing crops, surveying fields and wheat harvesting with sickles, scribe of accounts tabulating records), and Middle Kingdom model boat with rowing crew from Beni Hasan.
    - **Ancient Greece:** Attic black-figure amphora by the Antimenes Painter (olive harvest knocking olives with poles and collecting into baskets), Attic black-figure eye-kylix (potter assembling a kylix on the potter's wheel with workshop shelf of finished vases), Attic white-ground alabastron signed by master potter Pasiades (*Pasiades epoiesen*), Archaic bronze statuette of a ploughman driving a yoked pair of draft oxen with an ard-plow, and Classical marble grave stele of the shoemaker Xanthippos holding a shoemaker's last (*kalopous*).
    - **Ancient Rome & Roman Britain:** Funerary relief of freedmen artisans (*liberti* Publius Licinius Philonicus and Demetrius) depicting carved blacksmith tools (anvil, tongs, die hammer) and carpenter tools (axe, adze, rule), Roman marble relief from Carthage of a merchant sailor navigating a coastal cargo vessel (*corbita*), Roman bronze surgical instruments set (catheters, specula, probes), and Roman ink leaf-tablet from Vindolanda Fort (Tablet 343: quartermaster letter concerning wheat supplies, hides, and sinews).
    - **Ancient Mesopotamia (Late Uruk & Neo-Assyrian):** Proto-cuneiform clay tablet from southern Iraq (BM 140855: earliest known administrative account recording daily barley beer and grain rations for laborers), and the monumental Sennacherib Nineveh palace wall relief series across 5 contiguous panels illustrating the transport of a 30-ton colossal winged bull (*lamassu*) (hauling out of the quarry on sledge, tool-bearers with saws and pickaxes, work gangs pulling cables under taskmasters, rollers and shaduf water-lifters along the river, and palace ramp ascent).
  - **Data Bundling & Seed Pipeline Integration:**
    - Downloaded and verified all 21 image assets into `code/backend/data/images/bm_<safe_inventory_number>.jpg` with magic-byte verification (`\xff\xd8\xff`) and size constraints (<10MB) per `security-rules.md`.
    - Created [bm_ancient_workers.json](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/backend/data/bm_ancient_workers.json) containing structured JSON records with dimensions, dates, findspots, materials, tags, and detailed academic descriptions.
    - Created standalone idempotent seed file [bm_ancient_workers.sql](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/backend/data/bm_ancient_workers.sql).
    - Merged all 21 records into [filtered_small.sql](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/backend/data/filtered_small.sql), expanding the seed dataset from 39 to 60 total artifacts.
    - Updated [schemas.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/backend/src/schemas.py) and [object_service.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/code/backend/src/services/object_service.py) to normalize British Museum collection URLs to local proxy endpoints.
    - Created comprehensive catalog artifact [bm_ancient_workers_dataset.md](file:///Users/asafkedar/.gemini/antigravity-ide/brain/acb83af7-2cdf-4ab7-a97d-8da17a99aab7/bm_ancient_workers_dataset.md).

---

## [ACTIVE BACKLOG]

### [BLOCKED]
- None currently.

### [IN PROGRESS]
- **Deploy British Museum Dataset to Main:** Commit changes on `staging`, push to remotes, open PR to `main`, verify CI status checks, and merge into production.

### [PENDING]
- **Verify Live Production Deployment:** Inspect live Railway deployment logs to confirm successful migration and seeding of the 60 total artifacts (Met + British Museum).
