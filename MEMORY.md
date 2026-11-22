# PROJECT MEMORY HUB (Tier 1 — Hot Memory)

> Read this first every cycle. Load deep nodes only when the task touches their domain. Gate every write with `python3 .agents/scripts/memory_manager.py --fix`.

## [SYSTEM STATE]
### Tech Stack
- **Backend:** FastAPI (Python 3.10), SQLAlchemy 2.0, Alembic, PostgreSQL (`psycopg2-binary`), Boto3 (S3/MinIO/Tigris). Entrypoint `code/backend/src/main.py`; `PYTHONPATH=/app/src`.
- **Frontend:** React 19, Vite 7, TailwindCSS v4, React Router 7, Axios (`withCredentials: true`, `paramsSerializer: { indexes: null }`), Leaflet. API base `/api` (same-origin).
- **Infra:** Railway dual-service (public Nginx frontend → private `backend.railway.internal:8000` over IPv6 mesh). Local: `deployment/docker-compose.yml` (Postgres 15, MinIO, backend, frontend).
- **Boot sequence:** `alembic upgrade head && python seed_db.py && uvicorn src.main:app --host '::'`.

### Current Facts
- Seed catalog: **61 artifacts** (12 baseline Met + 27 Met ancient workers + 21 British Museum + 1 `0–899 CE` Vatican gold-glass roundel `60788` from `2_excel`), idempotently enriched from verified museum APIs & published corpora (`0` `'Unknown'` dates; unverified fields remain `NULL`), images served via `/api/images/{key}` (with `/placeholder-artifact.svg` fallback for pending uploads).
- Schema & Search: Aligned with `2_excel` (`f2b3c4d5e6f7`), assembled scholarly captions, multi-image `db_identifier` (`<id>.<seq>`), alphabetical `/tags`, default `title:asc` search sort (+ `date`/`location`/`material`), `0–899 CE` preset, and native `<dialog>` zoom/pan `ImageLightbox`.
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
| "When/why did we change X?" — Cycles 4–31 history | [archive.md](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/.agents/memory/archive.md) |

**Expansion protocol:** new domain → new node in `.agents/memory/` with a backlink to `MEMORY.md` + a row above. New root-cause bug → new `INV-<AREA>-NN` row in `lessons_and_invariants.md`. Cycles leaving the rolling window → `archive.md`.

## [PRODUCTION STRUCTURE]
### Backend core — `code/backend/src/`
- [main.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/main.py): Routes, middleware (trace ID, CORS, rate limit, bot defense), auth endpoints, `/api/images/{key}` proxy, honeypots, `/robots.txt`.
- [config.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/config.py): Env config; `postgres://` normalization; MinIO/AWS/Railway bucket aliases.
- [database.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/database.py): SQLAlchemy engine, session factory, declarative base.
- [models.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/models.py): `User`, `Source`, `Tag`, `Image`, `Object`, `DiscoveryKeyword`, `image_tags`.
- [schema.sql](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/schema.sql): Reference DDL (Alembic is the source of truth).
- [schemas.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/schemas.py): Pydantic I/O; `UserLogin` honeypots; `ReviewUpdate` `Literal`; `ImageResponse.normalize_file_url`.
- [auth.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/auth.py): bcrypt hashing, JWT creation, cookie auth dependencies.
- [bot_defense.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/bot_defense.py): `BotJail`, `LoginRateLimiter`, scanner UA regex, `extract_client_ip`, `reset_bot_defense_state`.
- [url_validator.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/url_validator.py): SSRF allowlists (`ALLOWED_IMAGE_DOMAINS`, `ALLOWED_API_DOMAINS`, `ALLOWED_SCHEMES`).
- [exceptions.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/exceptions.py): Domain exceptions (`EntityNotFoundError`, `ValidationError`).
- [logger.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/logger.py): Structured JSON logging with trace IDs.
- [object_repository.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/repositories/object_repository.py): Queries, eager loading, search/tag filters, field whitelist.
- [object_service.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/services/object_service.py): Business logic, bucket auto-caching, URL normalization, `SQLAlchemyError` handling.
- [museum_discovery_service.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/services/museum_discovery_service.py): Predefined open-access museum adapters (`met`, `cma`, `aic`, `vam`), duplicate index, full-field mapping, pending import.
- [s3_service.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/services/s3_service.py): S3 client, magic bytes, chunked uploads, SSRF-safe downloads, `ensure_stored_in_bucket`.

### Backend data collection — `code/backend/datacollection/`
- [data_ingest.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/datacollection/data_ingest.py): Met Museum API ingestion.
- [british_museum_ingest.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/datacollection/british_museum_ingest.py): British Museum ingestion.
- [ingestion_utils.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/datacollection/ingestion_utils.py): Shared parsing/tag helpers.
- [cache_utils.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/datacollection/cache_utils.py), [s3_utils.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/datacollection/s3_utils.py): Thin delegates to `s3_service`.
- [url_validator.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/datacollection/url_validator.py): Re-export of `src/url_validator.py`.

### Backend ops & data
- [seed_db.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/seed_db.py): Idempotent boot seeder (SQL, legacy URL rewrite, bucket migration, admins).
- [Dockerfile](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/Dockerfile), [requirements.txt](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/requirements.txt), `alembic/versions/` (`d86f7k1a32b9_initial_schema.py`, `e1a2b3c4d5e6_add_review_status_to_objects.py`, `f2b3c4d5e6f7_align_schema_with_2_excel.py`, `a1b2c3d4e5f8_add_discovery_keywords_table.py`, `b2c3d4e5f6a9_seed_datacollection_discovery_keywords.py`).
- `data/`: [filtered_small.sql](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/data/filtered_small.sql) (all 61), `met_ancient_workers.{json,sql}`, `bm_ancient_workers.{json,sql}`, `images/` — see `data_and_catalog.md`.

### Backend tests — `code/backend/tests/`
- [test_main.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/tests/test_main.py): API, auth, search/tags, image proxy, security remediations.
- [test_bot_defense.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/tests/test_bot_defense.py): Jail, login limiter, scanners, honeypots.
- [test_s3_service.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/tests/test_s3_service.py): SSRF, size limits, magic bytes, S3 errors.
- [test_seed_db.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/tests/test_seed_db.py): Seeder, URL rewrite, bucket migration.
- [test_ingestion.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/tests/test_ingestion.py): Data collection pipeline.
- [test_museum_discovery.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/tests/test_museum_discovery.py): Admin museum discovery, SSRF allowlist, dedup, and pending import tests.
- [test_memory_integrity.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/tests/test_memory_integrity.py): Memory auditor + live repo memory health gate.

### Frontend — `code/frontend/src/`
- Shell: [main.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/main.jsx), [App.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/App.jsx) (routes), [App.css](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/App.css), [index.css](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/index.css).
- Services/utils: [api.js](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/services/api.js), [AuthContext.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/contexts/AuthContext.jsx), [discoveryStream.js](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/utils/discoveryStream.js), [mapClustering.js](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/utils/mapClustering.js).
- Hooks: [useArtifacts.js](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/hooks/useArtifacts.js), [useObject.js](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/hooks/useObject.js), [useTags.js](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/hooks/useTags.js), [useMapData.js](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/hooks/useMapData.js).
- Components: [Layout.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/components/Layout.jsx) (honeypot link), [ArtifactGrid.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/components/ArtifactGrid.jsx), [FilterSidebar.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/components/FilterSidebar.jsx), [MapVisualizer.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/components/MapVisualizer.jsx), [ImageLightbox.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/components/ImageLightbox.jsx).
- Pages: [LandingPage.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/pages/LandingPage.jsx), [SearchPage.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/pages/SearchPage.jsx), [ObjectPage.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/pages/ObjectPage.jsx), [EditObjectPage.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/pages/EditObjectPage.jsx), [DiscoveryPage.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/pages/DiscoveryPage.jsx), [ReviewPage.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/pages/ReviewPage.jsx), [MapPage.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/pages/MapPage.jsx), [LoginPage.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/pages/LoginPage.jsx).
- Tests: [ArtifactGrid.test.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/test/ArtifactGrid.test.jsx), [CatalogEnhancements.test.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/test/CatalogEnhancements.test.jsx), [DiscoveryPage.test.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/test/DiscoveryPage.test.jsx), [MapClustering.test.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/test/MapClustering.test.jsx), [setup.js](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/test/setup.js).
- Edge/build: [nginx.conf.template](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/nginx.conf.template), [Dockerfile](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/Dockerfile), [vite.config.js](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/vite.config.js), [robots.txt](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/public/robots.txt).

### CI/CD — `.github/workflows/`
- [backend-ci.yml](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/.github/workflows/backend-ci.yml) (pytest, includes memory gate), [frontend-ci.yml](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/.github/workflows/frontend-ci.yml), [deploy-production.yml](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/.github/workflows/deploy-production.yml), [structure_check.yml](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/.github/workflows/structure_check.yml).

## [DOMAIN CONNECTIVITY MATRIX]
Touching one column? Check every other column in the same row.

| Feature slice | Backend | Frontend | Tests | Rules / Node |
| :--- | :--- | :--- | :--- | :--- |
| Search & tags | `main.py` `/objects/search`, `/tags` → `object_service` → `object_repository` | `useArtifacts`, `useTags`, `SearchPage`, `FilterSidebar`, `ArtifactGrid`, `api.js` serializer | `test_main.py::TestSearchAndTags`, `ArtifactGrid.test.jsx` | api-response, architecture node, INV-DB-03, INV-NET-03 |
| Object detail/edit/review | `/objects/{id}`, `PATCH /objects/{id}/review`, `schemas.ReviewUpdate` | `useObject`, `ObjectPage`, `EditObjectPage`, `ReviewPage` | `test_main.py::TestSecurityAuditRemediations` | security (mass assignment), INV-DB-04 |
| Admin museum discovery | `/admin/discovery/{museums,keywords,search,search/stream,import}`, `museum_discovery_service`, `url_validator` | `DiscoveryPage`, `discoveryStream`, `Layout`, `App` | `test_museum_discovery.py`, `DiscoveryPage.test.jsx` | security + data nodes, INV-SEC-01, INV-UI-01 |
| Map & cluster filter | `/objects/map` (`findspot`), `/objects/search?ids=...` → `object_service` → `object_repository` | `MapPage`, `MapVisualizer`, `mapClustering`, `useMapData`, `SearchPage`, `FilterSidebar`, `useArtifacts` | `test_main.py::TestMapAndIdFiltering`, `MapClustering.test.jsx` | production, security, INV-UI-01 |
| Auth & sessions | `/auth/login`, `/auth/logout`, `auth.py`, `bot_defense.LoginRateLimiter` | `AuthContext`, `LoginPage` | `test_main.py::TestAuthLogin`, `test_bot_defense.py` | security node |
| Anti-bot | `bot_defense.py`, middleware, `/bot-trap` | `Layout` trap link, `robots.txt`, `nginx.conf.template` | `test_bot_defense.py` | security node, INV-SEC-03 |
| Images & storage | `/api/images/{key}`, `s3_service`, `url_validator`, `config` | `ArtifactGrid`, `ObjectPage` `<img>` | `test_s3_service.py`, `test_main.py::TestServeImage` | architecture + security nodes, INV-SEC-01 |
| Seed & catalog | `seed_db.py`, `data/*.sql/json`, `datacollection/*` | — | `test_seed_db.py`, `test_ingestion.py` | data node |
| Deploy/infra | `Dockerfile`, Alembic | `Dockerfile`, `nginx.conf.template`, `vite.config.js` | CI workflows | architecture node, INV-DB-01/02, INV-NET-01/02 |
| Memory system | `.agents/scripts/memory_manager.py` | — | `test_memory_integrity.py` | memory-backlog, INV-MEM-01 |

## [RECENT CHANGES]
- **Cycle 32 (Dynamic Map Marker Fusion & Active Map Cluster Search Filter):**
  - Added `findspot` to `/objects/map` (`schemas.py`, `object_repository.py`) and bounded `?ids=` filtering (`MAX_FILTER_IDS = 500`, `422` validation, `review_status == 'accepted'`) to `/objects/search` (`main.py`, `object_service.py`, `object_repository.py`).
  - Created Web-Mercator pixel clustering utility [mapClustering.js](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/utils/mapClustering.js) (`radiusPx = 56`, numeric `0` coord preservation per `INV-UI-01`), updated [MapVisualizer.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/components/MapVisualizer.jsx), [MapPage.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/pages/MapPage.jsx), and [index.css](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/index.css) with zoom-responsive numeric cluster badges linking to `/search?ids=...&map_label=...`.
  - Wired `selectedIds` & `mapClusterLabel` active pill + clearable sidebar `Map Selection` card into [SearchPage.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/pages/SearchPage.jsx), [FilterSidebar.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/components/FilterSidebar.jsx), and [useArtifacts.js](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/hooks/useArtifacts.js); added `TestMapAndIdFiltering` (`test_main.py`) & [MapClustering.test.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/test/MapClustering.test.jsx); archived Cycle 29 to `archive.md`.
- **Cycle 33 (Seed All `datacollection/keywords` Terms into Museum Discovery Search):**
  - Expanded `DEFAULT_KEYWORDS` (`museum_discovery_service.py` & `DiscoveryPage.jsx`) to all **62** unique terms combining the 8 curated defaults + 60 `,`-stripped terms from `datacollection/keywords`, bumped `DiscoverySearchRequest.keywords` `max_length` to `200` (`schemas.py`), and added Alembic revision `b2c3d4e5f6a9_seed_datacollection_discovery_keywords.py`.
  - Added scrollable chip containment in `DiscoveryPage.jsx`, verified file sync + 62-keyword search in `test_museum_discovery.py` and `test_main.py`, and archived Cycle 30 to `archive.md`.
- **Cycle 34 (Real-Time Discovery Progress Streaming & Accessible Search Loading Indicators):**
  - Refactored `MuseumDiscoveryService` (`prepare_discovery` + `discover_with_index`) with per-museum/keyword/detail `progress_callback` and `cancel_event`, added NDJSON `POST /admin/discovery/search/stream` (`main.py`), and added unbuffered `location = /api/admin/discovery/search/stream` (`nginx.conf.template`).
  - Built [discoveryStream.js](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/utils/discoveryStream.js), native CSS `<progress>` bar/spinner styles (`index.css` w/ forced-colors & reduced-motion fallbacks), and live dashboard (`Live Discovery Progress`, elapsed timer, cancel abort, per-museum pipeline cards, activity feed) in [DiscoveryPage.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/pages/DiscoveryPage.jsx), plus `AbortController` + skeleton/spinner feedback in [useArtifacts.js](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/hooks/useArtifacts.js), [ArtifactGrid.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/components/ArtifactGrid.jsx), and [SearchPage.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/pages/SearchPage.jsx); archived Cycle 31 to `archive.md`.

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
