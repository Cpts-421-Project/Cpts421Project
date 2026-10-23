# PROJECT MEMORY HUB (Tier 1 — Hot Memory)

> Read this first every cycle. Load deep nodes only when the task touches their domain. Gate every write with `python3 .agents/scripts/memory_manager.py --fix`.

## [SYSTEM STATE]
### Tech Stack
- **Backend:** FastAPI (Python 3.10), SQLAlchemy 2.0, Alembic, PostgreSQL (`psycopg2-binary`), Boto3 (S3/MinIO/Tigris). Entrypoint `code/backend/src/main.py`; `PYTHONPATH=/app/src`.
- **Frontend:** React 19, Vite 7, TailwindCSS v4, React Router 7, Axios (`withCredentials: true`, `paramsSerializer: { indexes: null }`), Leaflet. API base `/api` (same-origin).
- **Infra:** Railway dual-service (public Nginx frontend → private `backend.railway.internal:8000` over IPv6 mesh). Local: `deployment/docker-compose.yml` (Postgres 15, MinIO, backend, frontend).
- **Boot sequence:** `alembic upgrade head && python seed_db.py && uvicorn src.main:app --host '::'`.

### Current Facts
- Seed catalog: **60 artifacts** (12 baseline Met + 27 Met ancient workers + 21 British Museum), all images bundled in `code/backend/data/images/` and served via `/api/images/{key}`.
- Auth: JWT in HttpOnly cookie (`samesite="lax"`, `max_age=1800` = `ACCESS_TOKEN_EXPIRE_MINUTES`); case-insensitive username/email login; constant-time decoy hash.
- Security: multi-layer anti-bot (Nginx + `bot_defense.py` + honeypots), strict-HTTPS SSRF allowlist, 64 KB chunked uploads with magic-byte MIME, `UPDATABLE_OBJECT_FIELDS` whitelist.
- Git remotes: `origin` = `Cpts-421-Project/Cpts421Project` (Railway deploys `main`), `personal` = `asafked121/Cpts421Project`. Flow: `staging` → PR → `main`.

### Memory Architecture
- **Tier 1:** this file (≤ 260 lines, ≤ 3 recent cycles).
- **Tier 2:** `.agents/memory/*.md` deep nodes (ever-expanding, lossless).
- **Tier 3:** [memory_manager.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/.agents/scripts/memory_manager.py) auditor (`--fix` heals links, `--json` for machine output) + [test_memory_integrity.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/tests/test_memory_integrity.py) (runs in Backend CI, so memory drift fails the build).

### Governing Rules (`.agents/rules/`)
| Rule | Enforces |
| :--- | :--- |
| [memory-backlog.md](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/.agents/rules/memory-backlog.md) | 3-tier memory read → execute → expand/compact/verify loop |
| [security-rules.md](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/.agents/rules/security-rules.md) | XSS, cookies, SSRF, DoS bounds, uploads, mass assignment, secrets, CORS |
| [production.md](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/.agents/rules/production.md) | Error handling, structured logging, async I/O, 12-factor config |
| [good-maintainabilty-rule.md](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/.agents/rules/good-maintainabilty-rule.md) | SOLID, low coupling, DI, DRY/KISS |
| [clean-codebase-rule.md](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/.agents/rules/clean-codebase-rule.md) | No dead code, orphan files, or unused deps |
| [api-response-rule.md](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/.agents/rules/api-response-rule.md) | HTTP 204 handling, awaited mutation → refetch chains, visible errors |
| [test-rule.md](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/.agents/rules/test-rule.md) | AAA pattern, Normal/Edge/Extraordinary coverage, mocked I/O |

## [KNOWLEDGE GRAPH & DEEP MEMORY NODES]
| Load when the task touches… | Deep node |
| :--- | :--- |
| Docker, Nginx, Railway mesh, DNS, Alembic, S3 config, image proxy, repo/service layers | [architecture_and_infra.md](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/.agents/memory/architecture_and_infra.md) |
| Auth, cookies, bot defense, rate limits, SSRF, uploads, schema privileges | [security_and_defense.md](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/.agents/memory/security_and_defense.md) |
| Seed SQL/JSON, artifact catalog, `seed_db.py` pipeline, scrapers, URL normalization | [data_and_catalog.md](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/.agents/memory/data_and_catalog.md) |
| Debugging, migrations, regressions — check `INV-*` before changing infra/security | [lessons_and_invariants.md](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/.agents/memory/lessons_and_invariants.md) |
| "When/why did we change X?" — Cycles 4–24 history | [archive.md](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/.agents/memory/archive.md) |

**Expansion protocol:** new domain → new node in `.agents/memory/` with a backlink to `MEMORY.md` + a row above. New root-cause bug → new `INV-<AREA>-NN` row in `lessons_and_invariants.md`. Cycles leaving the rolling window → `archive.md`.

## [PRODUCTION STRUCTURE]
### Backend core — `code/backend/src/`
- [main.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/main.py): Routes, middleware (trace ID, CORS, rate limit, bot defense), auth endpoints, `/api/images/{key}` proxy, honeypots, `/robots.txt`.
- [config.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/config.py): Env config; `postgres://` normalization; MinIO/AWS/Railway bucket aliases.
- [database.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/database.py): SQLAlchemy engine, session factory, declarative base.
- [models.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/models.py): `User`, `Source`, `Tag`, `Image`, `Object`, `image_tags`.
- [schema.sql](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/schema.sql): Reference DDL (Alembic is the source of truth).
- [schemas.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/schemas.py): Pydantic I/O; `UserLogin` honeypots; `ReviewUpdate` `Literal`; `ImageResponse.normalize_file_url`.
- [auth.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/auth.py): bcrypt hashing, JWT creation, cookie auth dependencies.
- [bot_defense.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/bot_defense.py): `BotJail`, `LoginRateLimiter`, scanner UA regex, `extract_client_ip`, `reset_bot_defense_state`.
- [url_validator.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/url_validator.py): SSRF allowlists (`ALLOWED_IMAGE_DOMAINS`, `ALLOWED_API_DOMAINS`, `ALLOWED_SCHEMES`).
- [exceptions.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/exceptions.py): Domain exceptions (`EntityNotFoundError`, `ValidationError`).
- [logger.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/logger.py): Structured JSON logging with trace IDs.
- [object_repository.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/repositories/object_repository.py): Queries, eager loading, search/tag filters, field whitelist.
- [object_service.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/services/object_service.py): Business logic, bucket auto-caching, URL normalization, `SQLAlchemyError` handling.
- [s3_service.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/services/s3_service.py): S3 client, magic bytes, chunked uploads, SSRF-safe downloads, `ensure_stored_in_bucket`.

### Backend data collection — `code/backend/datacollection/`
- [data_ingest.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/datacollection/data_ingest.py): Met Museum API ingestion.
- [british_museum_ingest.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/datacollection/british_museum_ingest.py): British Museum ingestion.
- [ingestion_utils.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/datacollection/ingestion_utils.py): Shared parsing/tag helpers.
- [cache_utils.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/datacollection/cache_utils.py), [s3_utils.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/datacollection/s3_utils.py): Thin delegates to `s3_service`.
- [url_validator.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/datacollection/url_validator.py): Re-export of `src/url_validator.py`.

### Backend ops & data
- [seed_db.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/seed_db.py): Idempotent boot seeder (SQL, legacy URL rewrite, bucket migration, admins).
- [Dockerfile](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/Dockerfile), [requirements.txt](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/requirements.txt), `alembic/versions/` (`d86f7k1a32b9_initial_schema.py`, `e1a2b3c4d5e6_add_review_status_to_objects.py`).
- `data/`: [filtered_small.sql](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/data/filtered_small.sql) (all 60), `met_ancient_workers.{json,sql}`, `bm_ancient_workers.{json,sql}`, `images/` — see `data_and_catalog.md`.

### Backend tests — `code/backend/tests/`
- [test_main.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/tests/test_main.py): API, auth, search/tags, image proxy, security remediations.
- [test_bot_defense.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/tests/test_bot_defense.py): Jail, login limiter, scanners, honeypots.
- [test_s3_service.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/tests/test_s3_service.py): SSRF, size limits, magic bytes, S3 errors.
- [test_seed_db.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/tests/test_seed_db.py): Seeder, URL rewrite, bucket migration.
- [test_ingestion.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/tests/test_ingestion.py): Data collection pipeline.
- [test_memory_integrity.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/tests/test_memory_integrity.py): Memory auditor + live repo memory health gate.

### Frontend — `code/frontend/src/`
- Shell: [main.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/main.jsx), [App.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/App.jsx) (routes), [App.css](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/App.css), [index.css](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/index.css).
- Services/state: [api.js](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/services/api.js), [AuthContext.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/contexts/AuthContext.jsx).
- Hooks: [useArtifacts.js](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/hooks/useArtifacts.js), [useObject.js](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/hooks/useObject.js), [useTags.js](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/hooks/useTags.js), [useMapData.js](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/hooks/useMapData.js).
- Components: [Layout.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/components/Layout.jsx) (honeypot link), [ArtifactGrid.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/components/ArtifactGrid.jsx), [FilterSidebar.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/components/FilterSidebar.jsx), [MapVisualizer.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/components/MapVisualizer.jsx).
- Pages: [LandingPage.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/pages/LandingPage.jsx), [SearchPage.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/pages/SearchPage.jsx), [ObjectPage.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/pages/ObjectPage.jsx), [EditObjectPage.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/pages/EditObjectPage.jsx), [ReviewPage.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/pages/ReviewPage.jsx), [MapPage.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/pages/MapPage.jsx), [LoginPage.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/pages/LoginPage.jsx).
- Tests: [ArtifactGrid.test.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/test/ArtifactGrid.test.jsx), [setup.js](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/test/setup.js).
- Edge/build: [nginx.conf.template](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/nginx.conf.template), [Dockerfile](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/Dockerfile), [vite.config.js](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/vite.config.js), [robots.txt](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/public/robots.txt).

### CI/CD — `.github/workflows/`
- [backend-ci.yml](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/.github/workflows/backend-ci.yml) (pytest, includes memory gate), [frontend-ci.yml](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/.github/workflows/frontend-ci.yml), [deploy-production.yml](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/.github/workflows/deploy-production.yml), [structure_check.yml](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/.github/workflows/structure_check.yml).

## [DOMAIN CONNECTIVITY MATRIX]
Touching one column? Check every other column in the same row.

| Feature slice | Backend | Frontend | Tests | Rules / Node |
| :--- | :--- | :--- | :--- | :--- |
| Search & tags | `main.py` `/objects/search`, `/tags` → `object_service` → `object_repository` | `useArtifacts`, `useTags`, `SearchPage`, `FilterSidebar`, `ArtifactGrid`, `api.js` serializer | `test_main.py::TestSearchAndTags`, `ArtifactGrid.test.jsx` | api-response, architecture node, INV-DB-03, INV-NET-03 |
| Object detail/edit/review | `/objects/{id}`, `PATCH /objects/{id}/review`, `schemas.ReviewUpdate` | `useObject`, `ObjectPage`, `EditObjectPage`, `ReviewPage` | `test_main.py::TestSecurityAuditRemediations` | security (mass assignment), INV-DB-04 |
| Map | `/objects/map` → `object_service.get_map_data` | `useMapData`, `MapPage`, `MapVisualizer` | `test_main.py` | production (defensive DB errors) |
| Auth & sessions | `/auth/login`, `/auth/logout`, `auth.py`, `bot_defense.LoginRateLimiter` | `AuthContext`, `LoginPage` | `test_main.py::TestAuthLogin`, `test_bot_defense.py` | security node |
| Anti-bot | `bot_defense.py`, middleware, `/bot-trap` | `Layout` trap link, `robots.txt`, `nginx.conf.template` | `test_bot_defense.py` | security node, INV-SEC-03 |
| Images & storage | `/api/images/{key}`, `s3_service`, `url_validator`, `config` | `ArtifactGrid`, `ObjectPage` `<img>` | `test_s3_service.py`, `test_main.py::TestServeImage` | architecture + security nodes, INV-SEC-01 |
| Seed & catalog | `seed_db.py`, `data/*.sql/json`, `datacollection/*` | — | `test_seed_db.py`, `test_ingestion.py` | data node |
| Deploy/infra | `Dockerfile`, Alembic | `Dockerfile`, `nginx.conf.template`, `vite.config.js` | CI workflows | architecture node, INV-DB-01/02, INV-NET-01/02 |
| Memory system | `.agents/scripts/memory_manager.py` | — | `test_memory_integrity.py` | memory-backlog, INV-MEM-01 |

## [RECENT CHANGES]
- **Cycle 25 (Met Museum Ancient Workers Dataset):** Curated 27 Met artifacts (Egypt, Greece, Rome, Mesopotamia) into `met_ancient_workers.{json,sql}` and merged into `filtered_small.sql` (12 → 39). Merged PR [#43](https://github.com/Cpts-421-Project/Cpts421Project/pull/43) at `541c2d3`.
- **Cycle 26 (British Museum Ancient Workers Dataset):** Curated 21 BM artifacts into `bm_ancient_workers.{json,sql}` with magic-byte-verified images (`bm_<inv>.jpg`); merged into `filtered_small.sql` (39 → 60); BM URL normalization in `schemas.py` and `object_service.py`. Merged PR [#44](https://github.com/Cpts-421-Project/Cpts421Project/pull/44) at `32463be`.
- **Cycle 27 (Self-Correcting, Connected Memory System):**
  - Split monolithic 306-line `MEMORY.md` into a hub plus 5 deep nodes in `.agents/memory/`; moved Cycles 4–24 to `archive.md` with nothing dropped.
  - Added `lessons_and_invariants.md` registry (`INV-DB-01..04`, `INV-NET-01..03`, `INV-SEC-01..03`, `INV-MEM-01`), built from past incidents.
  - Added `.agents/scripts/memory_manager.py`: section/line/cycle budgets, link validation (incl. `#L` anchors, traversal/null-byte rejection), `--fix` auto-healing of `file://` links missing `/Cpts421Project/`, bidirectional node/rule connectivity, and 100% production-file mapping.
  - Fixed 60+ broken `file://` links and mapped 26 previously unmapped files. Checked every deep-node fact against the source and corrected 11 wrong details (e.g. Nginx bursts, `BotJail` params, seeder/validator function names).
  - Added `test_memory_integrity.py` (Normal/Edge/Extraordinary, AAA) — the live gate runs in Backend CI.
  - Rewrote `memory-backlog.md` rule for the 3-tier read → execute → expand/compact/verify loop.
  - Merged PR [#45](https://github.com/Cpts-421-Project/Cpts421Project/pull/45) into `main` at `c35dc83` with all 6 CI and Railway checks passing.

## [ACTIVE BACKLOG]
### [BLOCKED]
- None.

### [IN PROGRESS]
- None.

### [PENDING]
- **Verify live production deployment:** Inspect Railway logs to confirm migration + seeding of all 60 artifacts.
- **Security (seed_db.py, rule §8):** `get_default_admins` logs the generated production admin password in plaintext via `logger.warning`; replace it with a masked or one-time secure delivery.
- **Security (seed_db.py, rule §8):** Hardcoded dev fallback password `DEFAULT_ADMIN_PASSWORD` default in source; remove the literal and require the env var or generate one.
- **Memory gate scope:** Backend CI only triggers on `code/backend/**` PR paths; consider adding a memory audit step to `structure_check.yml` so memory-only PRs are also gated.
