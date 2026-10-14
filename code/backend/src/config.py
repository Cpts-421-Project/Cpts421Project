import os
from distutils.util import strtobool

class Config:
    """Environment configuration manager."""

    # Database
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL:
        POSTGRES_USER = os.environ.get("POSTGRES_USER")
        POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD")
        POSTGRES_DB = os.environ.get("POSTGRES_DB")
        POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")
        POSTGRES_PORT = os.environ.get("POSTGRES_PORT", "5432")

        if not all([POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB]):
            raise RuntimeError(
                "CRITICAL: Database credentials not configured. "
                "Set DATABASE_URL or POSTGRES_USER, POSTGRES_PASSWORD, and POSTGRES_DB."
            )
        DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    
    # Railway/Heroku provide postgres:// which SQLAlchemy 1.4+ rejects
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    # DB Pool Config
    DB_POOL_SIZE = int(os.environ.get("DB_POOL_SIZE", "15"))
    DB_MAX_OVERFLOW = int(os.environ.get("DB_MAX_OVERFLOW", "5"))

    # Auth
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
    if not JWT_SECRET_KEY:
        # Fails loudly in production if secret isn't set
        raise RuntimeError("CRITICAL: JWT_SECRET_KEY environment variable is missing.")
    
    # S3 / MinIO / Railway Storage Bucket
    MINIO_ENDPOINT = (
        os.environ.get("MINIO_ENDPOINT")
        or os.environ.get("AWS_ENDPOINT_URL")
        or os.environ.get("S3_ENDPOINT")
        or os.environ.get("TIGRIS_URI")
    )
    if not MINIO_ENDPOINT:
        raise RuntimeError("CRITICAL: Storage endpoint is missing. Set MINIO_ENDPOINT or AWS_ENDPOINT_URL.")

    MINIO_ACCESS_KEY = (
        os.environ.get("MINIO_ACCESS_KEY")
        or os.environ.get("AWS_ACCESS_KEY_ID")
        or os.environ.get("S3_ACCESS_KEY")
    )
    if not MINIO_ACCESS_KEY:
        raise RuntimeError("CRITICAL: Storage access key is missing. Set MINIO_ACCESS_KEY or AWS_ACCESS_KEY_ID.")

    MINIO_SECRET_KEY = (
        os.environ.get("MINIO_SECRET_KEY")
        or os.environ.get("AWS_SECRET_ACCESS_KEY")
        or os.environ.get("S3_SECRET_KEY")
    )
    if not MINIO_SECRET_KEY:
        raise RuntimeError("CRITICAL: Storage secret key is missing. Set MINIO_SECRET_KEY or AWS_SECRET_ACCESS_KEY.")

    MINIO_BUCKET = (
        os.environ.get("MINIO_BUCKET")
        or os.environ.get("AWS_BUCKET")
        or os.environ.get("BUCKET_NAME")
        or os.environ.get("AWS_S3_BUCKET")
        or "uploads"
    )
    MINIO_PUBLIC_URL = (
        os.environ.get("MINIO_PUBLIC_URL")
        or MINIO_ENDPOINT
        or "http://localhost:9000"
    )
    AWS_REGION = os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "auto"))
    
    # App General
    DEBUG = bool(strtobool(os.environ.get("DEBUG", "False")))

    # CORS — comma-separated origins; defaults cover local dev
    ALLOWED_ORIGINS = [
        origin.strip()
        for origin in os.environ.get(
            "ALLOWED_ORIGINS",
            "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173"
        ).split(",")
        if origin.strip()
    ]

config = Config()
