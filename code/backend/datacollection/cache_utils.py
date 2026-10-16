"""
Utility for checking whether an image URL is already cached in our storage bucket.
Delegates to the unified s3_service for DRY compliance.
"""
from src.services.s3_service import is_bucket_url
from src.config import config

MINIO_PUBLIC_URL = config.MINIO_PUBLIC_URL or "http://localhost:9000"


def is_locally_cached(file_url: str) -> bool:
    """Returns True if the image URL points to our storage bucket."""
    return is_bucket_url(file_url)
