# Data Catalog, Ingestion & Idempotent Seeding Pipeline

> **Connected Hub:** [MEMORY.md](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/MEMORY.md) | **Governing Rules:** [production.md](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/.agents/rules/production.md), [security-rules.md](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/.agents/rules/security-rules.md), [test-rule.md](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/.agents/rules/test-rule.md)

---

## 1. Curated Ancient Workers Artifact Catalog (60 Total Artifacts)
The project bundles 60 public-domain museum artifacts with pre-verified local image assets (`code/backend/data/images/`), eliminating runtime external network dependencies:
1. **Baseline Metropolitan Museum Dataset (12 Artifacts):**
   - Bundled in [filtered_small.sql](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/data/filtered_small.sql) and [data/reduced_dataset/filtered_small.sql](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/data/reduced_dataset/filtered_small.sql) (`met_<inventory_number>.jpg`).
2. **Curated Metropolitan Museum Ancient Workers Dataset (27 Artifacts):**
   - Structured Metadata: [met_ancient_workers.json](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/data/met_ancient_workers.json) | Standalone SQL: [met_ancient_workers.sql](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/data/met_ancient_workers.sql).
   - **Egypt:** Meketre Middle Kingdom models (granary with scribes, bakery/brewery, cattle stable, plowing oxen, slaughterhouse butchery, paddling/rowing crews, kitchen cooks, estate figure), New Kingdom Tomb of Rekhmire workshop facsimiles (brickmakers, sphinx sculptors, carpenters, bronze smelters, goldsmiths), Tomb of Nebamun & Ipuky artisans, Tomb of Sennedjem agricultural scenes, Henettawy shabti.
   - **Greece:** Amasis Painter lekythos (spinning wool & weaving at vertical loom), Hellenistic artisan & foundry youth bronzes, Archaic fountain-house hydria.
   - **Rome:** Marble amphora dock-porter relief, Cypriot terracotta relief lamps depicting enslaved workers.
   - **Mesopotamia (Ur III):** Copper foundation figures of King Ur-Namma and King Shulgi carrying mortar baskets.
3. **Curated British Museum Ancient Workers Dataset (21 Artifacts):**
   - Structured Metadata: [bm_ancient_workers.json](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/data/bm_ancient_workers.json) | Standalone SQL: [bm_ancient_workers.sql](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/data/bm_ancient_workers.sql).
   - **Egypt:** Tomb-chapel of Nebamun wall paintings (cattle inspection, geese count, wheat harvest, scribe of accounts), Beni Hasan Middle Kingdom rowing boat model.
   - **Greece:** Antimenes Painter olive harvest amphora, potter's wheel eye-kylix, Pasiades signed alabastron, bronze ploughman with oxen, grave stele of shoemaker Xanthippos.
   - **Rome & Roman Britain:** Funerary relief of freedmen blacksmith/carpenter tools, Carthage merchant sailor *corbita* relief, bronze surgical instrument set, Vindolanda ink leaf-tablet 343.
   - **Mesopotamia (Late Uruk & Neo-Assyrian):** Proto-cuneiform laborer barley/beer ration tablet (`BM 140855`), and 5-panel Sennacherib Nineveh palace wall relief series depicting work gangs hauling a 30-ton *lamassu*.

---

## 2. Idempotent Deployment Seeding Pipeline ([seed_db.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/seed_db.py))
Executed automatically on container boot (`alembic upgrade head && python seed_db.py`):
1. **`execute_sql_file`:** Parses and runs [filtered_small.sql](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/data/filtered_small.sql) idempotently using `ON CONFLICT DO NOTHING` and `WHERE NOT EXISTS` guards.
2. **`update_legacy_image_urls`:** Rewrites any legacy external Met Museum (`collectionapi.metmuseum.org` / `images.metmuseum.org`) or British Museum URLs in PostgreSQL `images.file_url` to `/api/images/met_<inv>.jpg` or `/api/images/bm_<inv>.jpg`.
3. **`migrate_external_images_to_bucket`:** Uploads bundled local image files (`code/backend/data/images/`) to the configured S3/Tigris/MinIO bucket first (zero external network traffic), falling back to SSRF-validated streaming download only if a local bundle asset does not exist.
4. **`seed_admin_users`:** Upserts admin accounts from `get_default_admins()` with bcrypt-hashed passwords sourced from environment variables or CSPRNG tokens.
5. **`get_database_summary`:** Logs post-seed row counts; orchestrated end-to-end by `run_seeder`.

---

## 3. Multi-Layer Image URL Normalization
To guarantee no external third-party URLs leak to browser `<img>` tags:
1. **Service Layer ([object_service.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/services/object_service.py)):**
   - `create_object` & `update_object` pass all incoming `file_url` strings through `s3_service.ensure_stored_in_bucket`.
   - `_enrich_object_dict` runs `_normalize_image_url` on every returned object.
2. **Schema Serialization Layer ([schemas.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/schemas.py)):**
   - `ImageResponse.normalize_file_url` (`@field_validator("file_url", mode="before")`) rewrites legacy Met, British Museum, or internal `http://minio:9000` URLs into `/api/images/<key>` before JSON serialization.

---

## 4. Data Collection & Scraper Modules (`code/backend/datacollection/`)
- [data_ingest.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/datacollection/data_ingest.py): Metropolitan Museum of Art API ingestion pipeline.
- [british_museum_ingest.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/datacollection/british_museum_ingest.py): British Museum collection ingestion pipeline.
- [ingestion_utils.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/datacollection/ingestion_utils.py): Shared metadata parsing, coordinate normalization, and tag extraction helpers.
- [cache_utils.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/datacollection/cache_utils.py) & [s3_utils.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/datacollection/s3_utils.py): Delegate S3 caching and bucket uploads directly to [s3_service.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/services/s3_service.py).
- [url_validator.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/datacollection/url_validator.py): Re-exports SSRF validation from [src/url_validator.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/url_validator.py).
- **Tests:** [test_ingestion.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/tests/test_ingestion.py), [test_seed_db.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/tests/test_seed_db.py).

