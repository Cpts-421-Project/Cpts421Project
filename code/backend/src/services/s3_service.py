"""
S3 and MinIO Cloud Storage Service.
Unified interface for uploading, validating, and caching artifact photos in our storage bucket.
Enforces SSRF prevention, MIME magic-byte verification, and strict payload size limits.
"""
import uuid
from pathlib import PurePosixPath
from typing import Any, Optional, Tuple
from urllib.parse import unquote, urlparse
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from fastapi import UploadFile
import requests

from ..config import config
from ..exceptions import StorageError, ValidationError
from ..logger import app_logger
from ..url_validator import is_safe_image_url

s3_client = None

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

USER_AGENT = "AcademicArtifactDB/1.0 (Research Project)"
IMAGE_ACCEPT_HEADER = "image/avif,image/webp,image/apng,image/*,*/*;q=0.8"

IMAGE_MAGIC_BYTES = {
    b'\xff\xd8\xff': ('jpg', 'image/jpeg'),
    b'\x89PNG\r\n\x1a\n': ('png', 'image/png'),
    b'RIFF': ('webp', 'image/webp'),
    b'GIF87a': ('gif', 'image/gif'),
    b'GIF89a': ('gif', 'image/gif'),
}


def get_s3_client():
    """Initializes and caches the Boto3 S3 client using application config."""
    global s3_client
    if s3_client is None:
        try:
            boto_config = Config(
                signature_version='s3v4',
                s3={'addressing_style': 'path'},
                request_checksum_calculation='when_required',
                response_checksum_validation='when_required',
            )
        except TypeError:
            boto_config = Config(
                signature_version='s3v4',
                s3={'addressing_style': 'path'},
            )
        s3_client = boto3.client(
            's3',
            endpoint_url=config.MINIO_ENDPOINT,
            aws_access_key_id=config.MINIO_ACCESS_KEY,
            aws_secret_access_key=config.MINIO_SECRET_KEY,
            region_name=config.AWS_REGION,
            config=boto_config,
        )
    return s3_client


def validate_magic_bytes(content: bytes) -> Tuple[str, str]:
    """
    Validates that binary content matches known image signatures.
    Returns (extension, mime_type).
    Raises ValidationError if the signature is invalid or unrecognized.
    """
    if not content:
        raise ValidationError("Empty file payload received.")

    for magic, (ext, mime) in IMAGE_MAGIC_BYTES.items():
        if content.startswith(magic):
            return ext, mime

    raise ValidationError(
        f"Content does not match any allowed image signature (JPEG, PNG, WebP, GIF). "
        f"Header hex: {content[:8].hex()}"
    )


def _is_safe_proxy_key(key: str) -> bool:
    """Validate that an S3 object key is non-empty and free of path traversal."""
    unquoted_key = unquote(key)
    if (
        not key
        or "\x00" in key
        or "\x00" in unquoted_key
        or "\\" in key
        or "\\" in unquoted_key
        or key.startswith("~")
        or unquoted_key.startswith("~")
    ):
        return False
    posix_path = PurePosixPath(unquoted_key)
    if posix_path.is_absolute() or ".." in posix_path.parts:
        return False
    return True


def normalize_bucket_url_to_proxy(url: Optional[str]) -> Optional[str]:
    """
    Normalize direct S3/MinIO/Tigris bucket URLs or bare /images/ paths to our
    same-origin /api/images/{key} proxy path so browser <img> tags never hit
    private bucket endpoints or CSP-blocked HTTP URLs.
    """
    if not url or not isinstance(url, str):
        return url

    stripped = url.strip()
    if not stripped:
        return url

    if stripped.startswith("/api/images/"):
        return stripped

    if stripped.startswith("/images/"):
        key = stripped[len("/images/"):].lstrip("/")
        if _is_safe_proxy_key(key):
            return f"/api/images/{key}"
        return stripped

    parsed = urlparse(stripped)
    if parsed.scheme.lower() not in ("http", "https") or not parsed.netloc:
        return stripped

    netloc_lower = parsed.netloc.lower()
    hostname_lower = (parsed.hostname or "").lower()

    configured_hosts = set()
    configured_netlocs = set()
    for base in (config.MINIO_ENDPOINT, config.MINIO_PUBLIC_URL):
        if base and isinstance(base, str) and base.strip().lower().startswith(("http://", "https://")):
            b_parsed = urlparse(base.strip())
            if b_parsed.hostname:
                configured_hosts.add(b_parsed.hostname.lower())
            if b_parsed.netloc:
                configured_netlocs.add(b_parsed.netloc.lower())

    is_bucket_host = (
        hostname_lower in configured_hosts
        or netloc_lower in configured_netlocs
        or netloc_lower in {"minio:9000", "localhost:9000", "127.0.0.1:9000"}
        or hostname_lower == "storageapi.dev"
        or hostname_lower.endswith(".storageapi.dev")
        or hostname_lower == "storage.railway.app"
        or hostname_lower.endswith(".storage.railway.app")
    )
    if not is_bucket_host:
        return stripped

    key = parsed.path.lstrip("/")
    bucket_prefixes = {
        b.strip().lower()
        for b in (config.MINIO_BUCKET or "uploads", "uploads")
        if b and b.strip()
    }
    for bkt in bucket_prefixes:
        if key.lower().startswith(f"{bkt}/"):
            key = key[len(bkt) + 1:]
            break

    if not _is_safe_proxy_key(key):
        return stripped

    return f"/api/images/{key}"


def is_bucket_url(url: Optional[str]) -> bool:
    """
    Checks whether a URL points to our own storage bucket rather than an external CDN.
    """
    if not url or not isinstance(url, str):
        return False

    url_lower = url.lower().strip()

    # Internal bucket endpoints / proxy
    if url_lower.startswith("/api/images/") or url_lower.startswith("/images/"):
        return True

    bucket_name = (config.MINIO_BUCKET or "uploads").lower()

    # Check against configured public URL or endpoint
    for base in [config.MINIO_PUBLIC_URL, config.MINIO_ENDPOINT]:
        if base:
            clean_base = base.lower().rstrip('/')
            if clean_base and clean_base in url_lower:
                return True

    # Check path or host style matching the bucket name
    if f"/{bucket_name}/" in url_lower:
        return True
    if f"{bucket_name}." in url_lower:
        return True

    return False


def upload_bytes_to_minio(
    content: bytes,
    content_type: Optional[str] = None,
    file_name: Optional[str] = None,
    prefix: str = "obj"
) -> str:
    """
    Uploads raw binary content to our storage bucket and returns our internal image proxy URL.
    """
    if len(content) > MAX_FILE_SIZE_BYTES:
        app_logger.warning("Upload rejected: File size exceeded limit")
        raise ValidationError(f"File size exceeds maximum allowed limit of {MAX_FILE_SIZE_MB}MB.")

    detected_ext, detected_mime = validate_magic_bytes(content)
    # Always trust magic-byte detected MIME for cloud storage metadata
    final_mime = detected_mime

    if not file_name:
        file_name = f"{prefix}_{uuid.uuid4().hex[:8]}.{detected_ext}"
    else:
        # Guarantee extension aligns with detected image type
        base_name = file_name.rsplit(".", 1)[0]
        file_name = f"{base_name}.{detected_ext}"

    try:
        client = get_s3_client()
        client.put_object(
            Bucket=config.MINIO_BUCKET,
            Key=file_name,
            Body=content,
            ContentType=final_mime
        )
        return f"/api/images/{file_name}"
    except ClientError as e:
        app_logger.error("Boto3 ClientError during upload", exc_info=True)
        raise StorageError(f"Cloud storage error: {e.response.get('Error', {}).get('Message', str(e))}")
    except Exception as e:
        app_logger.error("Unexpected error during file upload", exc_info=True)
        raise StorageError(f"Unexpected upload failure: {str(e)}")


def upload_file_to_minio(file: UploadFile) -> str:
    """Uploads a FastAPI UploadFile to MinIO / S3 and returns the public URL."""
    content_type = file.content_type
    if content_type and content_type not in ALLOWED_MIME_TYPES:
        app_logger.warning("Upload rejected: Invalid MIME type %s", content_type)
        raise ValidationError(f"Invalid file type. Allowed types: {ALLOWED_MIME_TYPES}")

    # Stream chunks to avoid loading oversized files into memory (DoS protection)
    chunks = []
    total_size = 0
    chunk_size = 64 * 1024  # 64 KB
    while True:
        chunk = file.file.read(chunk_size)
        if not chunk:
            break
        total_size += len(chunk)
        if total_size > MAX_FILE_SIZE_BYTES:
            app_logger.warning("Upload rejected: File size exceeded limit during streaming")
            raise ValidationError(f"File size exceeds maximum allowed limit of {MAX_FILE_SIZE_MB}MB.")
        chunks.append(chunk)

    content = b"".join(chunks)
    detected_ext, detected_mime = validate_magic_bytes(content)
    file_name = f"manual_{uuid.uuid4().hex[:8]}.{detected_ext}"

    return upload_bytes_to_minio(content, content_type=detected_mime, file_name=file_name)


def _fetch_validated_image_bytes(image_url: str) -> Optional[Tuple[bytes, str, str]]:
    """Download an SSRF-validated external image with size limits and magic-byte verification."""
    if not is_safe_image_url(image_url):
        app_logger.warning("External download rejected by SSRF allowlist", extra={"url": image_url})
        return None

    response = requests.get(
        image_url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": IMAGE_ACCEPT_HEADER,
        },
        timeout=15,
        stream=True,
    )
    try:
        final_url = getattr(response, "url", None)
        if isinstance(final_url, str) and final_url and not is_safe_image_url(final_url):
            app_logger.warning(
                "External download redirect rejected by SSRF allowlist",
                extra={"url": final_url},
            )
            return None

        response.raise_for_status()

        # SEC-07: Stream with size limit
        chunks = []
        total = 0
        for chunk in response.iter_content(chunk_size=8192):
            if not chunk:
                continue
            total += len(chunk)
            if total > MAX_FILE_SIZE_BYTES:
                app_logger.warning("Image download exceeded size limit", extra={"url": image_url})
                return None
            chunks.append(chunk)

        content = b"".join(chunks)
        detected_ext, detected_mime = validate_magic_bytes(content)
        return content, detected_ext, detected_mime
    finally:
        if hasattr(response, "close"):
            response.close()


def download_and_store_image(
    image_url: str,
    object_identifier: Any = None,
    prefix: str = "obj",
    custom_filename: Optional[str] = None,
) -> Optional[str]:
    """
    Downloads an image from a validated external URL (SSRF & DoS safe),
    uploads it to our own bucket, and returns our internal proxy URL.
    Returns None if validation, download, or upload fails.
    """
    if not image_url or not isinstance(image_url, str):
        return None

    if is_bucket_url(image_url):
        return image_url

    if not is_safe_image_url(image_url):
        app_logger.warning("External download rejected by SSRF allowlist", extra={"url": image_url})
        return None

    candidate_urls = [image_url]
    if "images.metmuseum.org" in image_url.lower() and "/original/" in image_url:
        fallback_url = image_url.replace("/original/", "/web-large/", 1)
        if fallback_url != image_url and is_safe_image_url(fallback_url):
            candidate_urls.append(fallback_url)

    fetched: Optional[Tuple[bytes, str, str]] = None
    for idx, candidate_url in enumerate(candidate_urls):
        try:
            fetched = _fetch_validated_image_bytes(candidate_url)
            if fetched is not None:
                break
        except Exception as exc:
            app_logger.warning(
                "Failed downloading external image candidate (%d/%d): %s",
                idx + 1,
                len(candidate_urls),
                exc,
                exc_info=True,
                extra={"url": candidate_url},
            )

    if fetched is None:
        return None

    content, detected_ext, detected_mime = fetched

    if custom_filename:
        file_name = custom_filename if custom_filename.endswith(f".{detected_ext}") else f"{custom_filename}.{detected_ext}"
    else:
        safe_id = "".join(c if c.isalnum() else "_" for c in str(object_identifier)) if object_identifier else uuid.uuid4().hex[:8]
        file_name = f"{prefix}_{safe_id}_{uuid.uuid4().hex[:6]}.{detected_ext}"

    try:
        return upload_bytes_to_minio(
            content=content,
            content_type=detected_mime,
            file_name=file_name,
            prefix=prefix
        )
    except Exception as exc:
        app_logger.warning("Failed to pipe external image to storage bucket", exc_info=True, extra={"url": image_url})
        return None


def ensure_stored_in_bucket(
    image_url: str,
    object_identifier: Any = None,
    prefix: str = "obj"
) -> str:
    """
    Ensures that the image URL is stored on our bucket.
    If it is already on our bucket, returns as-is.
    If it is an external URL, downloads and stores it in our bucket.
    If download fails, returns original URL with warning (graceful degradation).
    """
    if not image_url or not isinstance(image_url, str):
        return image_url

    if is_bucket_url(image_url):
        return image_url

    cached_url = download_and_store_image(
        image_url,
        object_identifier=object_identifier,
        prefix=prefix
    )
    if cached_url:
        return cached_url

    app_logger.warning(
        "Could not migrate image to our bucket; falling back to original URL",
        extra={"image_url": image_url}
    )
    return image_url
