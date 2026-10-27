# Security, Authentication & Anti-Bot Defense Matrix

> **Connected Hub:** [MEMORY.md](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/MEMORY.md) | **Governing Rule:** [security-rules.md](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/.agents/rules/security-rules.md)

---

## 1. Multi-Layer Anti-Bot & Abuse Defense
Implemented across Nginx edge, FastAPI middleware, Pydantic schemas, and React components:
- **Edge Layer ([nginx.conf.template](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/nginx.conf.template)):**
  - Maps malicious scanner User-Agents (`$bad_bot`) to HTTP `403`.
  - Rejects exploit probe extensions/paths (`.env`, `.git`, `.php`, `.asp`, `.jsp`, `wp-`, `xmlrpc.php`) with HTTP `444` (connection closed without response).
  - Enforces rate-limiting zones: `api_limit` (`30r/s`, burst `50`) and `login_limit` (`5r/m`, burst `2`) returning HTTP `429`.
  - Sets `X-Real-IP: $remote_addr` so upstream rate limiters cannot be bypassed via spoofed `X-Forwarded-For` headers.
- **Backend Bot Defense Engine ([bot_defense.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/bot_defense.py)):**
  - `BotJail`: Temporary IP ban store (`default_ban_duration=3600.0`, `max_capacity=5000`) with automatic TTL eviction and bounded capacity to prevent memory exhaustion DoS.
  - `LoginRateLimiter`: Sliding-window limiter (`max_requests_per_window=10` per `window_seconds=60.0`) plus consecutive failure lockout (`max_consecutive_failures=5` → `lockout_duration_seconds=900.0`), bounded at `max_capacity=5000`.
  - `is_scanner_user_agent`: Regex signature detection (`sqlmap`, `nikto`, `acunetix`, `dirbuster`, `gobuster`, `nuclei`, `wpscan`, `masscan`, `zgrab`, `censys`, `shodan`, `nmap`).
- **FastAPI Middleware & Honeypot Traps ([main.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/main.py)):**
  - `bot_defense_middleware`: Blocks jailed IPs (`403`), jails scanner User-Agents (`403`), blocks exploit probes (`403`), and rejects empty User-Agents on mutating methods (`POST`, `PUT`, `PATCH`, `DELETE`).
  - Honeypot routes (`/bot-trap`, `/api/bot-trap` on `GET`/`POST`): Immediately jails any client or crawler accessing them.
- **Frontend Traps & Crawler Policy:**
  - [robots.txt](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/public/robots.txt): Disallows `/api/`, `/auth/`, `/bot-trap`, `/upload-images`, sets `Crawl-delay: 5`, and blocks AI scrapers (`GPTBot`, `CCBot`, `Bytespider`, `ClaudeBot`, `Anthropic-AI`, `Scrapy`).
  - [Layout.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/components/Layout.jsx): Renders an `aria-hidden` offscreen link to `/api/bot-trap` to catch automated link-following crawlers.
  - [LoginPage.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/pages/LoginPage.jsx), [AuthContext.jsx](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/frontend/src/contexts/AuthContext.jsx), & [schemas.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/schemas.py): Hidden `website`/`honeypot` input field on `UserLogin`; form bots auto-filling it are rejected (`400`) and jailed.

---

## 2. Authentication, Session Security & Timing Mitigation
- **HttpOnly Cookie Transport ([auth.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/auth.py) & [main.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/main.py)):**
  - JWTs are stored exclusively in `HttpOnly` cookies (`samesite="lax"`, `max_age=1800` aligned with `ACCESS_TOKEN_EXPIRE_MINUTES = 30`). Never stored in `localStorage`.
  - `/auth/logout` clears the cookie with matching `path="/"`, `httponly=True`, and `samesite="lax"`.
- **Constant-Time Login & Identifier Masking ([main.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/main.py)):**
  - Supports case-insensitive login by either `username` or `email` via `func.lower()`.
  - When a user is not found, verifies the password against `DUMMY_PASSWORD_HASH` in constant time to prevent user-enumeration timing attacks.
  - Masks user identifiers in structured logs (`identifier[:2] + "***"`).
- **Zero Hardcoded Secrets ([seed_db.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/seed_db.py)):**
  - `get_default_admins` reads admin passwords from env vars (`ADMIN_HALLIE_PASSWORD`/`ADMIN_PASSWORD_1`, `ADMIN_ASAF_PASSWORD`/`ADMIN_PASSWORD_2`/`ADMIN_PASSWORD`) or generates `secrets.token_urlsafe(18)` in production (`RAILWAY_ENVIRONMENT` or `ENVIRONMENT=production`).

---

## 3. SSRF, File Upload & Mass Assignment Defenses
- **Strict HTTPS SSRF Allowlist ([url_validator.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/url_validator.py)):**
  - Enforces `ALLOWED_SCHEMES = frozenset({"https"})` and `ALLOWED_IMAGE_DOMAINS = frozenset({"images.metmuseum.org", "collectionapi.metmuseum.org", "media.britishmuseum.org", "www.britishmuseum.org", "www.metmuseum.org"})` and `ALLOWED_API_DOMAINS` (`collectionapi.metmuseum.org`, `www.britishmuseum.org`).
- **Chunked Upload Streaming & Magic Bytes ([s3_service.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/services/s3_service.py)):**
  - Streams uploads in `64 KB` chunks with early abort at `MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024` (10 MB).
  - Inspects leading magic bytes (`validate_magic_bytes` for JPEG, PNG, WebP, GIF) and forces S3 `ContentType` and UUID filename extension to the verified magic-byte MIME type.
- **Schema Privilege Separation & Mass Assignment ([schemas.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/schemas.py) & [object_repository.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/src/repositories/object_repository.py)):**
  - `ObjectBase` excludes `review_status`; only authenticated admins can transition state via `PATCH /objects/{id}/review` using `ReviewUpdate` (`Literal["accepted", "rejected", "pending"]`).
  - `ObjectRepository.update_object` enforces `UPDATABLE_OBJECT_FIELDS` whitelist before calling `setattr`.

---

## 4. Verification Test Suites
- [test_bot_defense.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/tests/test_bot_defense.py): Unit & integration tests for `BotJail`, `LoginRateLimiter`, scanner UA blocking, honeypots, and exploit probes.
- [test_main.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/tests/test_main.py): `TestAuthLogin`, `TestSecurityAuditRemediations`, and `TestServeImage` suites.
- [test_s3_service.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/tests/test_s3_service.py): SSRF blocking, payload size limit, and magic-byte verification tests.

