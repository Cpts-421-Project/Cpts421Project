"""
S3/MinIO upload utility with SSRF protection, payload size limits, and MIME validation.
Delegates to unified src.services.s3_service for DRY compliance and consistent configuration.
"""
from typing import Any, Optional
from src.config import config
from src.services.s3_service import (
    download_and_store_image,
    upload_bytes_to_minio,
    validate_magic_bytes,
    get_s3_client,
    MAX_FILE_SIZE_BYTES,
    USER_AGENT,
    IMAGE_MAGIC_BYTES,
)
from src.url_validator import is_safe_image_url

MINIO_ENDPOINT = config.MINIO_ENDPOINT
MINIO_ACCESS_KEY = config.MINIO_ACCESS_KEY
MINIO_SECRET_KEY = config.MINIO_SECRET_KEY
MINIO_PUBLIC_URL = config.MINIO_PUBLIC_URL
BUCKET_NAME = config.MINIO_BUCKET
MAX_IMAGE_BYTES = MAX_FILE_SIZE_BYTES

_get_s3_client = get_s3_client


def _validate_magic_bytes(content: bytes) -> str:
    ext, _ = validate_magic_bytes(content)
    return ext


def download_and_upload_to_minio(image_url: str, object_identifier: Any, prefix: str = "obj") -> Optional[str]:
    """
    Downloads an image from a validated URL, validates its content, and uploads to MinIO.
    Preserved for backwards compatibility with existing ingestion scripts.
    """
    return download_and_store_image(image_url, object_identifier=object_identifier, prefix=prefix)
