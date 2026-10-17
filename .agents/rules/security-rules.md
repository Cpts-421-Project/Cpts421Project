---
trigger: always_on
---

# Security & Vulnerability Prevention Rules

You MUST ALWAYS adhere strictly to the following security guidelines when writing, modifying, or reviewing code. Security is a top priority, and you must proactively defend against common attack vectors and design flaws.

---

## 1. Cross-Site Scripting (XSS) & Content Security
- **NEVER use `innerHTML` or `outerHTML`** to render unsanitized user-generated content or API data.
- Always use `DOMPurify.sanitize()` prior to injecting any dynamic HTML.
- **NEVER use inline JavaScript event handlers** (e.g., `onclick="..."`, `onsubmit="..."`, `oninput="..."`). 
- **DOMPurify Configuration:** Never override DOMPurify to allow dangerous attributes like `onclick` or `onerror`.
- **Event Handling:** Use global Event Delegation with safe `data-*` attributes (`data-action`, `data-id`) and attach event listeners dynamically in JavaScript files.
- **Security Headers:** Production reverse proxies (e.g., Nginx) and servers must emit `Content-Security-Policy` (CSP), `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, and `Strict-Transport-Security` (HSTS).

---

## 2. Authentication, Session Management & Timing Attack Prevention
- **No Client Token Storage:** NEVER store JWTs, access tokens, or sensitive credentials in `localStorage` or `sessionStorage`.
- **HttpOnly Secure Cookies:** Always use **HttpOnly, Secure, and SameSite (Strict/Lax)** cookies for session management to protect against XSS token theft. Ensure backend endpoints (`/login`, `/logout`) correctly set and clear these cookies.
- **Cookie Deletion Consistency:** When calling `delete_cookie`, always supply matching `path="/"`, `httponly=True`, and `samesite` attributes so browsers reliably invalidate the session.
- **Timing Attack Mitigation (User Enumeration):** Login and password-verification endpoints must execute in constant time. If a user identifier (username/email) is not found in the database, always execute a decoy verification against a precomputed dummy hash (e.g., `verify_password(password, DUMMY_HASH)`) before returning HTTP 401.
- **Token Expiration Alignment:** Ensure JWT expiration matches the cookie `max_age` (e.g., 30 minutes) rather than maintaining long-lived 24h tokens behind short-lived cookies.

---

## 3. Server-Side Request Forgery (SSRF) Prevention
Whenever the backend fetches external resources (images, APIs, webhooks) based on user input or database URLs:
- **Parse and Validate:** Always parse the URL using standard libraries (`urllib.parse`).
- **Strict HTTPS Scheme:** Enforce strictly `scheme == 'https'`. Reject `http://` or other schemes to eliminate cleartext tampering and HTTP downgrade SSRF.
- **Enforce Hostname Allowlist:** Hostnames must match a strictly defined, immutable allowlist (`frozenset`). Reject all unrecognized hostnames, internal IPs, localhost, cloud metadata endpoints (`169.254.169.254`), and link-local addresses.
- **Strict Timeouts & Size Limits:** Always set a short timeout (`timeout=10`) and stream data with a hard byte-count limit to prevent hanging requests.

---

## 4. Denial of Service (DoS) & Resource Bounds
- **Bounded In-Memory Structures:** Any in-memory cache, rate-limiter dictionary, or state tracker MUST enforce an upper limit (`MAX_ENTRIES`) and automatic eviction/pruning for expired keys. Never allow an in-memory dictionary to grow unbounded with client-supplied keys.
- **Client IP Resolution & Anti-Spoofing:** When behind a reverse proxy (Nginx), NEVER trust the leftmost entry of `X-Forwarded-For` from untrusted clients. Use proxy-set headers like `X-Real-IP` (derived directly from `$remote_addr`) to prevent attackers from bypassing rate limits with spoofed IP headers.
- **Chunked Streaming for Uploads:** Never call `file.read()` all at once on uploaded files without verifying payload length. Always read file uploads in chunks (e.g., 64 KB) with an accumulated size check, aborting immediately with HTTP 400 if the payload exceeds `MAX_FILE_SIZE_BYTES`.
- **Data Parsing Limits:** When parsing complex files (e.g., CSV, Excel, XML, JSON), always enforce processing limits (e.g., `nrows=1000`) and safe parsers to prevent memory exhaustion or XML entity expansion (billion-laughs) attacks.

---

## 5. File Uploads, Magic Bytes & Storage Integrity
- **Magic-Byte Signature Verification:** Never trust client-supplied `Content-Type` headers or filename extensions. Always inspect the leading bytes (`magic bytes`) of uploaded content to verify true file type (JPEG, PNG, WebP, GIF, etc.).
- **Forced Storage MIME & Extension:** When saving to blob storage (S3/MinIO) or the local filesystem, force the object's `ContentType` and filename extension to the verified magic-byte type, ignoring arbitrary client-provided headers or extensions.
- **Deterministic & Safe Filenames:** Never preserve user-controlled filenames directly on disk or bucket storage. Generate secure names using UUIDs (`uuid.uuid4().hex`) or sanitized alphanumeric identifiers.

---

## 6. Mass Assignment & Schema Privilege Escalation
- **Strict Separation of Privileges in Schemas:** Public create/update schemas (e.g., `ObjectCreate`, `ObjectUpdate`, `UserUpdate`) MUST NOT expose internal administrative or state fields (e.g., `review_status`, `is_admin`, `role`, `verified`). State transitions must occur exclusively through dedicated, authenticated administrative endpoints (e.g., `PATCH /objects/{id}/review`).
- **Whitelist Updatable Attributes:** Database repositories and services must NEVER iterate over unvalidated input dictionaries with `setattr(model, key, value)`. Always check against an explicit, immutable whitelist (`UPDATABLE_FIELDS = frozenset({...})`).
- **Strict Enum/Literal Validation:** Status fields, state parameters, and query modes must be validated with `Literal[...]` or `Enum` in Pydantic models. Never accept unrestricted `str` for domain states.

---

## 7. Path Traversal & Parameter Sanitization
- **Path Traversal Defense:** When resolving filesystem paths or object storage keys:
  - Reject null bytes (`\x00`) and home directory expansion (`~`).
  - Strip leading slashes and normalize separators (`\` to `/`).
  - Parse with `PurePosixPath` and guarantee that `".." not in path.parts` and `not path.is_absolute()`.
- **Database ID Boundary Checks:** Never use truthiness (`if entity_id:`) to check IDs, as ID `0` is falsy. Always use explicit `if entity_id is not None:`.

---

## 8. Secrets Management & PII Hygiene
- **Zero Secrets in Code:** NEVER hardcode passwords, API keys, database credentials, or JWT signing keys in source code, seed files, migration scripts, or test fixtures.
  - Always read from environment variables (`.env`).
  - Seeding scripts must load admin passwords from environment variables or generate cryptographically secure random passwords via `secrets.token_urlsafe(18)` in production.
- **PII & Credential Masking in Logs:** Never log plaintext passwords, access tokens, or raw user identifiers in structured logs. Log masked identifiers (e.g., `identifier[:2] + "***"`) to prevent credential leakage in logging aggregators.

---

## 9. Injection Defense & CORS Hardening
- **Parameterized SQL Only:** Always use parameterized queries or ORM abstractions (SQLAlchemy). Never construct raw SQL strings via concatenation or f-strings.
- **Command Injection Prevention:** Avoid invoking shell commands with untrusted input (`subprocess.run(..., shell=True)`). If system commands are mandatory, pass arguments as an explicit array (`shell=False`).
- **Explicit CORS Configuration:** Never use wildcard methods (`allow_methods=["*"]`) or wildcard headers (`allow_headers=["*"]`) in conjunction with `allow_credentials=True`. Explicitly enumerate allowed methods (`GET, POST, PUT, PATCH, DELETE, OPTIONS`) and allowed headers (`Content-Type, Authorization, X-Trace-ID, Accept`).

---

## 🕵️ Pre-Commit Security Checklist
Before concluding any implementation or refactor, verify:
1. Did I introduce any hardcoded credentials, test passwords, or plaintext secrets?
2. Can a non-admin client self-approve or elevate privileges via the request schema?
3. Is client input validated against an explicit `Literal`, regex, or allowlist?
4. Does an in-memory dictionary or cache have an upper boundary and eviction policy?
5. Is file upload size validated in chunks during streaming, rather than loaded entirely into RAM?
6. Are MIME types and file extensions verified via magic bytes instead of trusting client headers?
7. Does login verify in constant time when users are not found?
8. Are paths checked against traversal with `PurePosixPath` and null byte detection?
9. Are CORS methods and headers explicitly enumerated?