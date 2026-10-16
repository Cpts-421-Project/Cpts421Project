"""
S3 and MinIO Cloud Storage Service.
Unified interface for uploading, validating, and caching artifact photos in our storage bucket.
Enforces SSRF prevention, MIME magic-byte verification, and strict payload size limits.
"""
import uuid
from typing import Any, Optional, Tuple
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
        s3_client = boto3.client(
            's3',
            endpoint_url=config.MINIO_ENDPOINT,
            aws_access_key_id=config.MINIO_ACCESS_KEY,
            aws_secret_access_key=config.MINIO_SECRET_KEY,
            region_name=config.AWS_REGION,
            config=Config(
                signature_version='s3v4',
                s3={'addressing_style': 'path'}
            )
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
    Uploads raw binary content to our storage bucket and returns the public bucket URL.
    """
    if len(content) > MAX_FILE_SIZE_BYTES:
        app_logger.warning("Upload rejected: File size exceeded limit")
        raise ValidationError(f"File size exceeds maximum allowed limit of {MAX_FILE_SIZE_MB}MB.")

    detected_ext, detected_mime = validate_magic_bytes(content)
    final_mime = content_type or detected_mime

    if not file_name:
        file_name = f"{prefix}_{uuid.uuid4().hex[:8]}.{detected_ext}"

    try:
        client = get_s3_client()
        client.put_object(
            Bucket=config.MINIO_BUCKET,
            Key=file_name,
            Body=content,
            ContentType=final_mime
        )
        if config.MINIO_PUBLIC_URL and config.MINIO_PUBLIC_URL.startswith("http"):
            base_url = config.MINIO_PUBLIC_URL.rstrip('/')
            return f"{base_url}/{config.MINIO_BUCKET}/{file_name}"
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
    if content_type not in ALLOWED_MIME_TYPES:
        app_logger.warning("Upload rejected: Invalid MIME type %s", content_type)
        raise ValidationError(f"Invalid file type. Allowed types: {ALLOWED_MIME_TYPES}")

    content = file.file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        app_logger.warning("Upload rejected: File size exceeded limit")
        raise ValidationError(f"File size exceeds maximum allowed limit of {MAX_FILE_SIZE_MB}MB.")

    file.file.seek(0)
    ext = file.filename.split(".")[-1].lower() if file.filename and "." in file.filename else "bin"
    file_name = f"manual_{uuid.uuid4().hex[:8]}.{ext}"

    return upload_bytes_to_minio(content, content_type=content_type, file_name=file_name)


def download_and_store_image(
    image_url: str,
    object_identifier: Any = None,
    prefix: str = "obj",
    custom_filename: Optional[str] = None,
) -> Optional[str]:
    """
    Downloads an image from a validated external URL (SSRF & DoS safe),
    uploads it to our own bucket, and returns our bucket public URL.
    Returns None if validation, download, or upload fails.
    """
    if not image_url or not isinstance(image_url, str):
        return None

    if is_bucket_url(image_url):
        return image_url

    if not is_safe_image_url(image_url):
        app_logger.warning("External download rejected by SSRF allowlist", extra={"url": image_url})
        return None

    try:
        response = requests.get(
            image_url,
            headers={"User-Agent": USER_AGENT},
            timeout=15,
            stream=True
        )
        response.raise_for_status()

        # SEC-07: Stream with size limit
        chunks = []
        total = 0
        for chunk in response.iter_content(chunk_size=8192):
            total += len(chunk)
            if total > MAX_FILE_SIZE_BYTES:
                app_logger.warning("Image download exceeded size limit", extra={"url": image_url})
                return None
            chunks.append(chunk)

        content = b"".join(chunks)
        detected_ext, detected_mime = validate_magic_bytes(content)

        if custom_filename:
            file_name = custom_filename if custom_filename.endswith(f".{detected_ext}") else f"{custom_filename}.{detected_ext}"
        else:
            safe_id = "".join(c if c.isalnum() else "_" for c in str(object_identifier)) if object_identifier else uuid.uuid4().hex[:8]
            file_name = f"{prefix}_{safe_id}_{uuid.uuid4().hex[:6]}.{detected_ext}"

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
