"""
Re-export URL validation utility from src.url_validator for backwards compatibility and DRY compliance.
"""
from src.url_validator import (
    ALLOWED_IMAGE_DOMAINS,
    ALLOWED_API_DOMAINS,
    ALLOWED_SCHEMES,
    URLValidationError,
    validate_url,
    is_safe_image_url,
)

__all__ = [
    "ALLOWED_IMAGE_DOMAINS",
    "ALLOWED_API_DOMAINS",
    "ALLOWED_SCHEMES",
    "URLValidationError",
    "validate_url",
    "is_safe_image_url",
]
