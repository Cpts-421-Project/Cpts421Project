import time
import uuid
from pathlib import Path, PurePosixPath
from typing import List, Optional
from datetime import timedelta

from fastapi import FastAPI, HTTPException, Query, Depends, Request, Response, UploadFile, File, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from botocore.exceptions import ClientError
from .config import config
from .database import get_db, get_engine, Base
from .schemas import ObjectDetailResponse, ObjectMapResponse, UserLogin, ObjectCreate, ObjectUpdate, ReviewUpdate
from .services.object_service import ObjectService
from .services.s3_service import upload_file_to_minio, get_s3_client, validate_magic_bytes
from .auth import verify_password, create_access_token, get_current_user, get_current_admin_user, ACCESS_TOKEN_EXPIRE_MINUTES
from .models import User
from .exceptions import BaseAppException
from .logger import app_logger
from .bot_defense import (
    extract_client_ip,
    is_malicious_user_agent,
    is_empty_user_agent,
    bot_jail,
    login_rate_limiter,
    EXPLOIT_PROBE_PATHS,
)

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    app_logger.info("Application starting up...")
    # Production Notice: Table schema should be driven by Alembic via `alembic upgrade head`.
    # Do NOT inject Base.metadata.create_all(bind=engine) here.
    yield
    app_logger.info("Application shutting down.")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Trace-ID", "Accept"],
)


# Exception handler for domain exceptions
@app.exception_handler(BaseAppException)
async def app_exception_handler(request: Request, exc: BaseAppException):
    app_logger.warning("Domain exception raised", extra={"status": exc.status_code, "detail": exc.message})
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )


# Logging and Trace ID Middleware
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))
    request.state.trace_id = trace_id
    
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    app_logger.info(
        "Request processed",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(process_time * 1000, 2),
            "trace_id": trace_id
        }
    )
    response.headers["X-Trace-ID"] = trace_id
    return response


# Rate limiter middleware
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX = 120    # max requests per window per IP
MAX_RATE_LIMIT_STORE = 10000  # Cap maximum tracked IPs to prevent memory exhaustion DoS
_rate_limit_store: dict = {}
_last_rate_limit_cleanup = 0.0

def _cleanup_rate_limit_store(now: float) -> None:
    """Evict expired rate limit entries to prevent memory exhaustion."""
    global _last_rate_limit_cleanup
    if now - _last_rate_limit_cleanup < 30.0 and len(_rate_limit_store) < MAX_RATE_LIMIT_STORE:
        return
    _last_rate_limit_cleanup = now

    expired_ips = [
        ip for ip, timestamps in _rate_limit_store.items()
        if not timestamps or (now - timestamps[-1] >= RATE_LIMIT_WINDOW)
    ]
    for ip in expired_ips:
        _rate_limit_store.pop(ip, None)

    if len(_rate_limit_store) >= MAX_RATE_LIMIT_STORE:
        overflow_count = len(_rate_limit_store) - (MAX_RATE_LIMIT_STORE // 2)
        for key in list(_rate_limit_store.keys())[:overflow_count]:
            _rate_limit_store.pop(key, None)

# Bot Defense Middleware
@app.middleware("http")
async def bot_defense_middleware(request: Request, call_next):
    client_ip = extract_client_ip(request)
    trace_id = getattr(request.state, "trace_id", None) or request.headers.get("X-Trace-ID", str(uuid.uuid4()))

    # 1. Reject immediately if IP is currently jailed
    if bot_jail.is_ip_banned(client_ip):
        app_logger.warning("Blocked request from jailed bot IP", extra={"ip": client_ip, "trace_id": trace_id})
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": "Access denied: automated bot activity detected."}
        )

    # 2. Check for Honeypot trap routes and common vulnerability scanner probes
    path = request.url.path.rstrip("/")
    if path in EXPLOIT_PROBE_PATHS or path.startswith("/.env") or path.startswith("/.git") or path.startswith("/wp-"):
        bot_jail.ban_ip(client_ip, duration=3600.0, reason=f"honeypot_probe:{path}")
        app_logger.warning(
            "Bot probe or honeypot trap accessed. IP banned.",
            extra={"ip": client_ip, "path": path, "trace_id": trace_id}
        )
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": "Access denied: automated bot activity detected."}
        )

    # 3. Detect known malicious scanner / exploit tool User-Agents
    user_agent = request.headers.get("user-agent", "")
    if is_malicious_user_agent(user_agent):
        bot_jail.ban_ip(client_ip, duration=3600.0, reason=f"malicious_user_agent:{user_agent[:50]}")
        app_logger.warning(
            "Malicious scanner User-Agent detected. IP banned.",
            extra={"ip": client_ip, "user_agent": user_agent, "trace_id": trace_id}
        )
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": "Access denied: automated security scanner detected."}
        )

    # 4. Enforce User-Agent on state-modifying endpoints (POST, PUT, PATCH, DELETE)
    if request.method in ("POST", "PUT", "PATCH", "DELETE") and is_empty_user_agent(user_agent):
        app_logger.warning(
            "State-modifying request rejected due to missing User-Agent",
            extra={"ip": client_ip, "method": request.method, "path": path, "trace_id": trace_id}
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "User-Agent header is required for state-modifying requests."}
        )

    return await call_next(request)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Safely resolve client IP via X-Real-IP (reverse proxy) or client host
    client_ip = extract_client_ip(request)

    now = time.time()
    _cleanup_rate_limit_store(now)

    timestamps = [
        t for t in _rate_limit_store.get(client_ip, []) if now - t < RATE_LIMIT_WINDOW
    ]

    if len(timestamps) >= RATE_LIMIT_MAX:
        app_logger.warning("Rate limit exceeded", extra={"ip": client_ip})
        return JSONResponse(
            content={"detail": "Rate limit exceeded. Try again later."},
            status_code=429
        )

    timestamps.append(now)
    _rate_limit_store[client_ip] = timestamps
    return await call_next(request)


@app.get("/bot-trap")
@app.get("/api/bot-trap")
@app.post("/bot-trap")
@app.post("/api/bot-trap")
async def bot_trap_endpoint(request: Request):
    """
    Invisible honeypot trap route. Human users never access this route.
    Any crawler or bot following this link is automatically banned.
    """
    client_ip = extract_client_ip(request)
    trace_id = getattr(request.state, "trace_id", "unknown")
    bot_jail.ban_ip(client_ip, duration=3600.0, reason="bot_trap_endpoint_accessed")
    app_logger.warning("Bot honeypot trap accessed. IP banned.", extra={"ip": client_ip, "trace_id": trace_id})
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": "Access denied: automated bot activity detected."}
    )


@app.get("/robots.txt", response_class=Response)
async def robots_txt_fallback():
    """Fallback robots.txt for direct API requests instructing crawlers."""
    content = (
        "# Academic Artifact Database robots.txt\n"
        "User-agent: *\n"
        "Disallow: /api/\n"
        "Disallow: /auth/\n"
        "Disallow: /bot-trap\n"
        "Disallow: /upload-images\n"
        "Crawl-delay: 5\n"
        "\n"
        "# Disallow aggressive AI scraper bots\n"
        "User-agent: GPTBot\n"
        "Disallow: /\n"
        "\n"
        "User-agent: CCBot\n"
        "Disallow: /\n"
        "\n"
        "User-agent: Bytespider\n"
        "Disallow: /\n"
        "\n"
        "User-agent: ClaudeBot\n"
        "Disallow: /\n"
        "\n"
        "User-agent: Scrapy\n"
        "Disallow: /\n"
    )
    return Response(content=content, media_type="text/plain")


@app.get("/")
async def read_root():
    return {"message": "Academic Artifact Research Database API"}


# Constant-time decoy hash for timing attack mitigation (precomputed bcrypt hash)
DUMMY_PASSWORD_HASH = "$2b$12$e80M5XqGvyf8y6vGj2d0eO6z0l6qY6G7K1h4N1x7Y3r7b5u9e2c6G"

# Custom Auth Endpoints Using HttpOnly Cookies
@app.post("/auth/login")
async def login(login_data: UserLogin, request: Request, response: Response, db: Session = Depends(get_db)):
    client_ip = extract_client_ip(request)
    trace_id = getattr(request.state, "trace_id", "unknown")

    # Anti-bot honeypot check: automated form submitters fill all fields
    if (login_data.honeypot and login_data.honeypot.strip()) or (login_data.website and login_data.website.strip()):
        bot_jail.ban_ip(client_ip, duration=3600.0, reason="login_honeypot_field_populated")
        app_logger.warning("Bot detected via honeypot form field. IP banned.", extra={"ip": client_ip, "trace_id": trace_id})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request submission.",
        )

    identifier = login_data.username.strip()
    masked_identifier = f"{identifier[:2]}***" if len(identifier) > 2 else "***"

    # Dedicated login rate limiter and brute-force lockout check
    is_allowed, rate_err = login_rate_limiter.check_login_attempt(client_ip, identifier)
    if not is_allowed:
        app_logger.warning(
            "Login attempt throttled",
            extra={"ip": client_ip, "identifier_prefix": masked_identifier, "detail": rate_err, "trace_id": trace_id}
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=rate_err or "Too many login attempts. Please try again later.",
        )

    def _do_login():
        return db.query(User).filter(
            or_(
                func.lower(User.username) == identifier.lower(),
                func.lower(User.email) == identifier.lower(),
            )
        ).first()

    user = await run_in_threadpool(_do_login)

    if not user:
        # Constant-time decoy verification prevents username enumeration via response latency
        verify_password(login_data.password, DUMMY_PASSWORD_HASH)
        login_rate_limiter.record_login_failure(client_ip, identifier)
        app_logger.warning("Failed login attempt", extra={"identifier_prefix": masked_identifier})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    if not verify_password(login_data.password, user.password_hash):
        login_rate_limiter.record_login_failure(client_ip, identifier)
        app_logger.warning("Failed login attempt", extra={"identifier_prefix": masked_identifier})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    # Successful login resets failed attempt counters
    login_rate_limiter.record_login_success(client_ip, identifier)

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    is_production = config.IS_PRODUCTION
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=1800,
        expires=1800,
        samesite="lax",
        secure=is_production,
    )
    app_logger.info("User logged in successfully", extra={"username": user.username})
    return {"message": "Logged in successfully", "username": user.username, "is_admin": user.is_admin}


@app.post("/auth/logout")
async def logout(response: Response):
    is_production = config.IS_PRODUCTION
    response.delete_cookie(
        "access_token",
        path="/",
        httponly=True,
        samesite="lax",
        secure=is_production,
    )
    return {"message": "Logged out successfully"}


@app.get("/auth/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {"username": current_user.username, "is_admin": current_user.is_admin}


# Admin Object Management 
@app.post("/upload-images")
async def upload_images(files: List[UploadFile] = File(...), current_user: User = Depends(get_current_admin_user)):
    urls = []
    for f in files:
        url = await run_in_threadpool(upload_file_to_minio, f)
        urls.append(url)
    return {"urls": urls}


@app.post("/objects", response_model=ObjectDetailResponse)
async def create_object(object_data: ObjectCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    service = ObjectService(db)
    return await run_in_threadpool(service.create_object, object_data.model_dump())


@app.put("/objects/{object_id}", response_model=ObjectDetailResponse)
async def update_object(object_id: int, object_data: ObjectUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    service = ObjectService(db)
    return await run_in_threadpool(service.update_object, object_id, object_data.model_dump())


@app.delete("/objects/{object_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_object(object_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    service = ObjectService(db)
    await run_in_threadpool(service.delete_object, object_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/objects/pending", response_model=List[ObjectDetailResponse])
async def get_pending_objects(db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    service = ObjectService(db)
    return await run_in_threadpool(service.get_pending_objects)


@app.patch("/objects/{object_id}/review", response_model=ObjectDetailResponse)
async def review_object(object_id: int, review_data: ReviewUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    service = ObjectService(db)
    result = await run_in_threadpool(service.update_object, object_id, {"review_status": review_data.status})
    if not result:
        raise HTTPException(status_code=404, detail="Object not found")
        
    if review_data.status == "rejected":
        # Keep only 3 most recent rejected, hard delete older
        from .models import Object
        rejected_objs = db.query(Object).filter(Object.review_status == 'rejected').order_by(Object.id.desc()).all()
        if len(rejected_objs) > 3:
            for obj_to_delete in rejected_objs[3:]:
                await run_in_threadpool(service.delete_object, obj_to_delete.id)
                
    return result


# Existing Endpoints
@app.get("/objects/search", response_model=List[ObjectDetailResponse])
async def search_objects(
    search: Optional[str] = Query(None, description="General search query across name, description, material, findspot, inventory number, tags"),
    q: Optional[str] = Query(None, description="Alias for search query"),
    tags: Optional[List[str]] = Query(None, description="Filter by tag names (matches objects containing any of the selected tags)"),
    tag: Optional[str] = Query(None, description="Single tag or comma-separated tags filter"),
    tag_mode: str = Query("any", pattern="^(any|all)$", description="Match 'any' (OR) or 'all' (AND) selected tags"),
    material: Optional[str] = Query(None, max_length=255),
    year: Optional[int] = Query(None, description="Fuzzy date search year"),
    date_start: Optional[int] = None,
    date_end: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    query_term = search or q
    # Parse tags from either repeated tags param, comma-separated strings, or single tag
    parsed_tags: List[str] = []
    if tags:
        for t in tags:
            parsed_tags.extend([item.strip() for item in t.split(",") if item.strip()])
    if tag:
        parsed_tags.extend([item.strip() for item in tag.split(",") if item.strip()])

    service = ObjectService(db)
    return await run_in_threadpool(
        service.search,
        material=material,
        year=year,
        date_start=date_start,
        date_end=date_end,
        search=query_term,
        tags=parsed_tags if parsed_tags else None,
        tag_mode=tag_mode,
        skip=skip,
        limit=limit,
    )


@app.get("/objects/map", response_model=List[ObjectMapResponse])
async def get_objects_map(db: Session = Depends(get_db)):
    service = ObjectService(db)
    return await run_in_threadpool(service.get_map_data)


@app.get("/tags", response_model=List[str])
async def get_tags(db: Session = Depends(get_db)):
    service = ObjectService(db)
    return await run_in_threadpool(service.get_all_tags)


@app.get("/objects/{object_id}", response_model=ObjectDetailResponse)
async def get_object_detail(object_id: int, db: Session = Depends(get_db)):
    service = ObjectService(db)
    return await run_in_threadpool(service.get_by_id, object_id)


@app.get("/images/{key:path}")
@app.get("/api/images/{key:path}")
async def serve_image(key: str):
    """
    Streams artifact images directly from our S3/MinIO bucket.
    If the image has not yet been synced to S3, falls back to the bundled local
    image assets and auto-caches it to the bucket.
    Enforces path traversal protection and cache headers.
    """
    if "\x00" in key or key.startswith("~"):
        raise HTTPException(status_code=400, detail="Invalid image path")

    clean_key = key.lstrip("/").replace("\\", "/")
    if ".." in clean_key or clean_key.startswith("/") or clean_key.startswith("~"):
        raise HTTPException(status_code=400, detail="Invalid image path")

    posix_path = PurePosixPath(clean_key)
    if ".." in posix_path.parts or posix_path.is_absolute():
        raise HTTPException(status_code=400, detail="Invalid image path")

    bucket = config.MINIO_BUCKET or "uploads"
    s3_key = clean_key
    if s3_key.startswith(f"{bucket}/"):
        s3_key = s3_key[len(bucket) + 1:]

    # 1. Attempt to stream from S3 / MinIO
    try:
        s3 = get_s3_client()
        response = await run_in_threadpool(s3.get_object, Bucket=bucket, Key=s3_key)
        content_type = response.get("ContentType", "image/jpeg")
        return StreamingResponse(
            response["Body"],
            media_type=content_type,
            headers={
                "Cache-Control": "public, max-age=86400",
                "X-Content-Type-Options": "nosniff",
            }
        )
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        if error_code not in ("NoSuchKey", "404", "AccessDenied", "NoSuchBucket"):
            app_logger.warning("S3 ClientError while serving %s: %s", s3_key, e)
    except Exception as exc:
        app_logger.warning("Error fetching %s from S3: %s", s3_key, exc)

    # 2. Fallback to bundled local images (e.g. met_241792.jpg)
    filename = Path(s3_key).name
    candidate_dirs = [
        Path(__file__).resolve().parent.parent / "data" / "images",
        Path(__file__).resolve().parent.parent.parent.parent / "data" / "reduced_dataset" / "images",
        Path("/app/data/images"),
        Path("data/images"),
    ]

    for candidate_dir in candidate_dirs:
        local_file = candidate_dir / filename
        if local_file.is_file():
            try:
                with open(local_file, "rb") as f:
                    content = f.read()
                try:
                    _, detected_mime = validate_magic_bytes(content)
                except Exception:
                    detected_mime = "image/jpeg"

                # Asynchronously cache into S3 bucket
                try:
                    s3 = get_s3_client()
                    await run_in_threadpool(
                        s3.put_object,
                        Bucket=bucket,
                        Key=s3_key,
                        Body=content,
                        ContentType=detected_mime
                    )
                    app_logger.info("Auto-cached local image %s into S3 bucket %s", s3_key, bucket)
                except Exception as cache_err:
                    app_logger.debug("Failed auto-caching %s to S3: %s", s3_key, cache_err)

                return Response(
                    content=content,
                    media_type=detected_mime,
                    headers={
                        "Cache-Control": "public, max-age=86400",
                        "X-Content-Type-Options": "nosniff",
                    }
                )
            except Exception as read_err:
                app_logger.error("Failed reading local fallback image %s: %s", local_file, read_err)

    raise HTTPException(status_code=404, detail=f"Image '{clean_key}' not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
