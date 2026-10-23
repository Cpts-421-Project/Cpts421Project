# Architecture, Infrastructure & Storage Topology

> **Connected Hub:** [MEMORY.md](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/MEMORY.md) | **Governing Rules:** [production.md](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/.agents/rules/production.md), [good-maintainabilty-rule.md](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/.agents/rules/good-maintainabilty-rule.md), [api-response-rule.md](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/.agents/rules/api-response-rule.md)

---

## 1. Dual-Service Private Mesh Architecture (Railway Production)

```
[Public Internet]
       │ HTTPS (Port 443 -> $PORT)
       ▼
┌──────────────────────────────────────────────────────────┐
│ Frontend Container (nginx:alpine)                        │
│ - Serves React 19 SPA static bundle (/usr/share/nginx)   │
│ - Enforces CSP, HSTS, X-Frame-Options, nosniff           │
│ - Blocks bad bots ($bad_bot -> 403) & exploit probes     │
│ - Rate limits /api/ (30r/s) and /api/auth/login (5r/m)   │
│ - Proxies /api/* with X-Real-IP: $remote_addr            │
└──────────────────────────┬───────────────────────────────┘
                           │ Railway WireGuard Private Mesh (IPv6 / Dual-Stack)
                           │ http://backend.railway.internal:8000
                           ▼
┌──────────────────────────────────────────────────────────┐
│ Backend Container (python:3.10-slim / Uvicorn --host ::) │
│ - Startup: alembic upgrade head && python seed_db.py     │
│ - Middleware: Trace ID, CORS, Rate Limit, Bot Defense    │
│ - REST API + Internal S3 Image Streamer (/api/images/*)  │
└───────────┬──────────────────────────────────┬───────────┘
            │ Internal TCP                     │ S3 Path-Style HTTPS/HTTP
            ▼                                  ▼
┌───────────────────────────┐    ┌─────────────────────────┐
│ PostgreSQL 15 Database    │    │ Tigris / S3 / MinIO     │
│ (DATABASE_URL normalized) │    │ Private Artifact Bucket │
└───────────────────────────┘    └─────────────────────────┘
```

### Key Infrastructure Files
- **Frontend Reverse Proxy Template:** [nginx.conf.template](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/nginx.conf.template)
- **Frontend Container Build:** [Dockerfile](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/Dockerfile)
- **Backend Container Build:** [Dockerfile](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/Dockerfile)
- **Local Multi-Container Orchestration:** [docker-compose.yml](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/deployment/docker-compose.yml)
- **CI/CD Pipelines:** [backend-ci.yml](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/.github/workflows/backend-ci.yml), [frontend-ci.yml](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/.github/workflows/frontend-ci.yml), [deploy-production.yml](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/.github/workflows/deploy-production.yml), [structure_check.yml](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/.github/workflows/structure_check.yml)

---

## 2. Reverse Proxy & Dynamic DNS Resolution
- **Dynamic DNS Discovery:** [Dockerfile](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/Dockerfile) extracts nameservers from `/etc/resolv.conf` at container boot and injects Railway's IPv6 internal DNS (`[fd12::10]`) and Docker DNS (`127.0.0.11`) into `$RESOLVER` via `envsubst`.
- **Variable `proxy_pass` Path Forwarding:** [nginx.conf.template](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/nginx.conf.template) uses named regex capture `location ~ ^/api/?(?<path>.*)$` with `proxy_pass $backend_target/$path$is_args$args;` so Nginx re-resolves DNS per TTL (`valid=10s`) without truncating the URI path.
- **IPv6 Dual-Stack Binding:** [Dockerfile](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/Dockerfile) starts Uvicorn with `--host '::'` so it accepts both IPv6 Railway WireGuard mesh connections and IPv4 Docker bridge traffic.

---

## 3. Unified Storage & Internal Image Proxy Architecture
- **Configuration Layer:** [config.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/config.py) normalizes environment variables across MinIO (`MINIO_*`), AWS/Tigris (`AWS_ENDPOINT_URL`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `BUCKET_NAME`), and Railway Storage Buckets (`ENDPOINT`, `ACCESS_KEY_ID`, `SECRET_ACCESS_KEY`, `RAILWAY_BUCKET_NAME`). Defaults `MINIO_PUBLIC_URL` to `/api/images`.
- **S3 Client Service:** [s3_service.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/services/s3_service.py) uses `boto3` configured with `s3={'addressing_style': 'path'}` for universal compatibility with MinIO and Tigris.
- **Direct Internal Bucket Proxy:** [main.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/main.py) exposes `/images/{key:path}` and `/api/images/{key:path}` (`serve_image`):
  1. Validates `key` via `PurePosixPath` against path traversal (`..`, `\`, leading `/`, `~`, `\x00`).
  2. Streams object directly from the private S3/Tigris bucket using backend credentials.
  3. Falls back to bundled seed assets in `code/backend/data/images/` if missing from the bucket and lazily uploads the asset to S3 in the background.
  4. Emits `Cache-Control: public, max-age=86400` and `X-Content-Type-Options: nosniff`.

---

## 4. Database & Migration Lifecycle
- **Engine & Session Management:** [database.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/database.py) & [models.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/models.py) define `User`, `Source`, `Tag`, `Image`, `Object`, and `image_tags`.
- **Alembic Versions:**
  - `code/backend/alembic/versions/d86f7k1a32b9_initial_schema.py`: Base tables.
  - `code/backend/alembic/versions/e1a2b3c4d5e6_add_review_status_to_objects.py`: Adds `review_status` column (`server_default=sa.text("'accepted'")`) and index `ix_objects_review_status`.
- **Repository & Service Separation:**
  - [object_repository.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/repositories/object_repository.py): Encapsulates SQLAlchemy queries, eager-loading (`joinedload(Object.images).joinedload(Image.tags)`), multi-field `ilike` search, `any`/`all` tag filtering, and `UPDATABLE_OBJECT_FIELDS` whitelisting.
  - [object_service.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/services/object_service.py): Orchestrates business logic, S3 image auto-caching (`ensure_stored_in_bucket`), legacy URL normalization (`_normalize_image_url`), and defensive `SQLAlchemyError` handling.

