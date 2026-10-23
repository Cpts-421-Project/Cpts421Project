# System Invariants & Root-Cause Lessons Learned

> **Connected Hub:** [MEMORY.md](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/MEMORY.md) | **Governing Rules:** [memory-backlog.md](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/.agents/rules/memory-backlog.md), [production.md](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/.agents/rules/production.md), [security-rules.md](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/.agents/rules/security-rules.md)

This node is an ever-expanding registry of architectural invariants and root-cause analyses. Before modifying infrastructure, migrations, proxies, or security middleware, consult these invariants to prevent regressions.

---

## 1. Database & Alembic Migration Invariants

| ID | Symptom / Incident | Root Cause | Permanent Invariant & Guard |
| :--- | :--- | :--- | :--- |
| **INV-DB-01** | `502 Bad Gateway` on Railway startup; PostgreSQL error `column "accepted" does not exist` (Cycle 8). | In Alembic `op.add_column`, passing unquoted `server_default='accepted'` causes PostgreSQL to interpret `accepted` as a column identifier rather than a string literal. | Always wrap string literal defaults in `sa.text("'value'")` inside Alembic migrations (e.g., `server_default=sa.text("'accepted'")`). |
| **INV-DB-02** | `500 Internal Server Error` on `/objects/search` and `/objects/map` after schema evolution (Cycle 7). | `models.py` added `Object.review_status` without a corresponding Alembic migration file in `alembic/versions/`. | Every SQLAlchemy column addition in [models.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/models.py) MUST be paired with an Alembic revision in `code/backend/alembic/versions/`. |
| **INV-DB-03** | N+1 query performance degradation when serializing `tags` on search results (Cycle 17). | Accessing `obj.images` and `img.tags` lazily per row triggered secondary queries. | Always eager-load `joinedload(Object.images).joinedload(Image.tags)` in [object_repository.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/repositories/object_repository.py). |
| **INV-DB-04** | Updating artifact metadata without a new `images` array wiped existing artifact photos (Cycle 21). | `ObjectService.update_object` passed `images_data=[]` when `images` was `None`. | Only replace images in [object_service.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/services/object_service.py) when `obj_in.images is not None`. |

---

## 2. Networking, Nginx & Railway Mesh Invariants

| ID | Symptom / Incident | Root Cause | Permanent Invariant & Guard |
| :--- | :--- | :--- | :--- |
| **INV-NET-01** | Frontend Nginx failed to connect to `backend.railway.internal:8000` over Railway private network (Cycle 6). | Uvicorn bound only to `0.0.0.0` (IPv4), while Railway's WireGuard private mesh routes over IPv6 (`fd12::/16`). | Always start Uvicorn with `--host '::'` in [Dockerfile](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/Dockerfile) for dual-stack IPv6 + IPv4 binding. |
| **INV-NET-02** | Nginx `proxy_pass` with variable host truncated `/api/objects/search` path (Cycle 7). | When `proxy_pass` uses a variable (to force DNS re-resolution), Nginx drops the URI suffix unless explicitly captured and appended. | Use regex location `location ~ ^/api/?(?<path>.*)$` with `proxy_pass $backend_target/$path$is_args$args;` in [nginx.conf.template](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/nginx.conf.template). |
| **INV-NET-03** | Axios serialized array query parameters as `tags[]=a&tags[]=b`, which FastAPI ignored (Cycle 17). | Axios defaults to bracket index notation for arrays, whereas FastAPI `Query()` expects repeated keys (`tags=a&tags=b`). | Maintain `paramsSerializer: { indexes: null }` on the Axios client in [api.js](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/services/api.js). |

---

## 3. Storage, Security & Test Isolation Invariants

| ID | Symptom / Incident | Root Cause | Permanent Invariant & Guard |
| :--- | :--- | :--- | :--- |
| **INV-SEC-01** | Browser `<img>` tags failed to load private bucket URLs or leaked external Met/BM URLs (Cycle 20). | Direct S3 endpoints require credentials or CORS policies, and legacy seed rows contained external museum URLs. | Serve all artifact images via the internal `/api/images/{key:path}` proxy in [main.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/main.py) and normalize URLs in [schemas.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/schemas.py) and [object_service.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/services/object_service.py). |
| **INV-SEC-02** | `EntityNotFoundError` omitted `entity_id` when `entity_id = 0` (Cycle 21). | Checked `if entity_id:` (truthiness) where `0` evaluates to `False`. | Always check `if entity_id is not None:` in [exceptions.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/exceptions.py). |
| **INV-SEC-03** | Rate-limiting and BotJail state leaked across unit tests causing false `403`/`429` failures (Cycle 24). | In-memory rate limiters persist across `TestClient` requests within the same pytest process. | Always call `reset_bot_defense_state()` in test setup fixtures in [test_main.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/tests/test_main.py) and [test_bot_defense.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/tests/test_bot_defense.py). |
| **INV-MEM-01** | Broken `file://` links (missing `/Cpts421Project/`) and unmapped frontend/backend files in `MEMORY.md` (Cycle 27). | Manual markdown edits lacked automated link resolution and filesystem completeness checks. | Run [memory_manager.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/.agents/scripts/memory_manager.py) (`--fix`) and [test_memory_integrity.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/tests/test_memory_integrity.py) on every memory update. |

