"""
Database Seeding Script for Academic Artifact Research Database.
Seeds initial sources, objects, images, tags, image_tags, and default admin users.

Idempotent: Safe to run multiple times without duplicating records.
Supports:
  - Local PostgreSQL / Docker Compose
  - Remote / Production PostgreSQL (Railway)
  - SQLite (testing / verification)
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import bcrypt
from sqlalchemy import create_engine, text, func
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

# Setup structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("seed_db")

# Default admin accounts to seed if not already present
DEFAULT_ADMINS = [
    {
        "email": "Hallie.Meredith@lincoln.oxon.org",
        "username": "halliemeredith",
        "password": "T@g^s,arE;fOUr379!PvrPle",
    },
    {
        "email": "asaf.kedar1@gmail.com",
        "username": "asafKedar",
        "password": "-EgX6nsEMfsAZW",
    },
]


def resolve_database_url(cli_url: Optional[str] = None) -> str:
    """
    Resolve and normalize the database connection URL.
    Checks CLI arg -> DATABASE_URL env var -> deployment/.env fallback.
    Normalizes 'postgres://' to 'postgresql://' for SQLAlchemy compatibility.
    """
    url = cli_url or os.environ.get("DATABASE_URL")

    if not url:
        # Check deployment/.env if present
        env_path = Path(__file__).resolve().parent.parent.parent / "deployment" / ".env"
        if env_path.is_file():
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("DATABASE_URL="):
                            url = line.split("=", 1)[1].strip().strip('"').strip("'")
                            break
            except Exception as e:
                logger.warning("Failed to parse %s: %s", env_path, e)

    if not url:
        raise ValueError(
            "Database URL not found. Pass --database-url or set the DATABASE_URL environment variable."
        )

    # Normalize Railway/Heroku URL scheme
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    return url


def find_default_sql_file() -> Path:
    """Find default filtered_small.sql path relative to repo or backend."""
    candidates = [
        Path(__file__).resolve().parent.parent.parent / "data" / "reduced_dataset" / "filtered_small.sql",
        Path(__file__).resolve().parent / "data" / "filtered_small.sql",
        Path("/app/data/filtered_small.sql"),
        Path("data/reduced_dataset/filtered_small.sql"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return candidates[0]


def execute_sql_file(engine: Engine, sql_file_path: Path) -> None:
    """
    Execute SQL script using raw DBAPI connection to avoid SQLAlchemy
    bind-parameter parsing issues with colons in URLs or text.
    """
    if not sql_file_path.is_file():
        raise FileNotFoundError(f"SQL file not found at: {sql_file_path}")

    logger.info("Reading SQL seed file from %s...", sql_file_path)
    with open(sql_file_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    logger.info("Executing SQL statements...")
    raw_conn = engine.raw_connection()
    try:
        cursor = raw_conn.cursor()
        if hasattr(cursor, "executescript"):
            # SQLite support
            cursor.executescript(sql_content)
        else:
            # PostgreSQL (psycopg2) supports multi-statement strings.
            # Enabling autocommit allows the SQL file's BEGIN...COMMIT to govern transactions cleanly.
            if hasattr(raw_conn, "autocommit"):
                raw_conn.autocommit = True
            cursor.execute(sql_content)
        cursor.close()
        logger.info("SQL seed executed and committed successfully.")
    except Exception as exc:
        try:
            if hasattr(raw_conn, "rollback"):
                raw_conn.rollback()
        except Exception:
            pass
        logger.error("Failed to execute SQL seed: %s", exc)
        raise
    finally:
        raw_conn.close()


def seed_admin_users(engine: Engine) -> None:
    """Seed initial administrator accounts if they do not already exist."""
    # Import models safely
    backend_src = str(Path(__file__).resolve().parent / "src")
    if backend_src not in sys.path:
        sys.path.insert(0, backend_src)

    from src.models import User

    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        for admin in DEFAULT_ADMINS:
            existing = session.query(User).filter(User.email == admin["email"]).first()
            if not existing:
                password_bytes = admin["password"].encode("utf-8")
                hashed_pw = bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")
                new_user = User(
                    email=admin["email"],
                    username=admin["username"],
                    password_hash=hashed_pw,
                    is_admin=True,
                )
                session.add(new_user)
                session.commit()
                logger.info("Created admin user: %s (%s)", admin["username"], admin["email"])
            else:
                logger.info("Admin user already exists: %s (%s)", admin["username"], admin["email"])
    except Exception as exc:
        session.rollback()
        logger.error("Error seeding admin users: %s", exc)
        raise
    finally:
        session.close()


def find_default_images_dir() -> Optional[Path]:
    """Find default directory containing pre-downloaded seed images."""
    candidates = [
        Path(__file__).resolve().parent / "data" / "images",
        Path(__file__).resolve().parent.parent.parent / "data" / "reduced_dataset" / "images",
        Path("/app/data/images"),
        Path("data/reduced_dataset/images"),
    ]
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    return None


def migrate_external_images_to_bucket(
    engine: Engine,
    images_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Scans the database for any Image records with external URLs.
    Migrates them into our storage bucket using pre-downloaded images if available,
    or streaming downloads from the external URL with SSRF/DoS protection.
    Updates the database with the new bucket URLs.
    """
    backend_src = str(Path(__file__).resolve().parent / "src")
    if backend_src not in sys.path:
        sys.path.insert(0, backend_src)

    from src.models import Image, Object
    from src.services.s3_service import is_bucket_url, upload_bytes_to_minio, download_and_store_image
    from src.config import config

    # Check if S3 credentials are configured
    if not config.MINIO_ACCESS_KEY or not config.MINIO_ENDPOINT:
        logger.warning(
            "Storage bucket credentials not configured. Skipping external image migration."
        )
        return {"total": 0, "migrated": 0, "failed": 0, "skipped": 0}

    resolved_images_dir = images_dir or find_default_images_dir()
    Session = sessionmaker(bind=engine)
    session = Session()

    stats = {"total": 0, "migrated": 0, "failed": 0, "skipped": 0}
    try:
        images = session.query(Image).all()
        external_images = [img for img in images if img.file_url and not is_bucket_url(img.file_url)]
        stats["total"] = len(external_images)

        if not external_images:
            logger.info("All %d images are already stored in our bucket.", len(images))
            return stats

        logger.info("Found %d external images to migrate into our storage bucket...", len(external_images))

        for img in external_images:
            obj = session.query(Object).filter(Object.id == img.object_id).first() if img.object_id else None
            inv_num = obj.inventory_number if obj else str(img.id)
            safe_inv = "".join(c if c.isalnum() else "_" for c in str(inv_num))
            target_filename = f"met_{safe_inv}.jpg"

            bucket_url = None

            # 1. Try local cached image file first (zero network overhead, instant & offline safe)
            if resolved_images_dir:
                local_path = resolved_images_dir / target_filename
                if local_path.is_file():
                    try:
                        with open(local_path, "rb") as f:
                            content = f.read()
                        bucket_url = upload_bytes_to_minio(
                            content=content,
                            content_type="image/jpeg",
                            file_name=target_filename
                        )
                        logger.info("Uploaded local seed image %s to bucket", target_filename)
                    except Exception as e:
                        logger.warning("Failed uploading local file %s to bucket: %s", local_path, e)

            # 2. If not local or local upload failed, try download from external URL
            if not bucket_url and img.file_url and img.file_url.startswith("http"):
                try:
                    bucket_url = download_and_store_image(
                        image_url=img.file_url,
                        object_identifier=inv_num,
                        prefix="met",
                        custom_filename=target_filename
                    )
                except Exception as e:
                    logger.warning("Failed downloading external image %s: %s", img.file_url, e)

            # 3. If successfully stored in bucket, update the record
            if bucket_url:
                old_url = img.file_url
                img.file_url = bucket_url
                stats["migrated"] += 1
                logger.info("Migrated photo for object %s: %s -> %s", inv_num, old_url, bucket_url)
            else:
                stats["failed"] += 1
                logger.warning("Could not migrate image for object %s (%s)", inv_num, img.file_url)

        session.commit()
        logger.info(
            "Image migration complete: %d migrated, %d failed out of %d total external images.",
            stats["migrated"], stats["failed"], stats["total"]
        )
    except Exception as exc:
        session.rollback()
        logger.error("Error during image migration to bucket: %s", exc)
        raise
    finally:
        session.close()

    return stats


def get_database_summary(engine: Engine) -> Dict[str, Any]:
    """Retrieve row counts across key tables for verification."""
    backend_src = str(Path(__file__).resolve().parent / "src")
    if backend_src not in sys.path:
        sys.path.insert(0, backend_src)

    from src.models import Object, Image, Source, Tag, User, image_tags
    from src.services.s3_service import is_bucket_url

    Session = sessionmaker(bind=engine)
    session = Session()
    summary = {}
    try:
        summary["total_objects"] = session.query(func.count(Object.id)).scalar() or 0
        summary["accepted_objects"] = (
            session.query(func.count(Object.id)).filter(Object.review_status == "accepted").scalar() or 0
        )
        summary["pending_objects"] = (
            session.query(func.count(Object.id)).filter(Object.review_status != "accepted").scalar() or 0
        )
        summary["total_images"] = session.query(func.count(Image.id)).scalar() or 0
        
        all_images = session.query(Image.file_url).all()
        summary["bucket_images"] = sum(1 for (url,) in all_images if url and is_bucket_url(url))
        summary["external_images"] = summary["total_images"] - summary["bucket_images"]

        summary["total_sources"] = session.query(func.count(Source.id)).scalar() or 0
        summary["total_tags"] = session.query(func.count(Tag.id)).scalar() or 0
        summary["total_image_tags"] = session.query(func.count()).select_from(image_tags).scalar() or 0
        summary["total_users"] = session.query(func.count(User.id)).scalar() or 0
        
        users = session.query(User.username, User.email, User.is_admin).all()
        summary["users"] = [{"username": u[0], "email": u[1], "is_admin": u[2]} for u in users]
    finally:
        session.close()

    return summary


def run_seeder(
    database_url: str,
    sql_file_path: Optional[Path] = None,
    seed_admins: bool = True,
    verify_only: bool = False,
    migrate_images: bool = True,
    images_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Main seeder orchestration function."""
    engine = create_engine(database_url, pool_pre_ping=True)

    if not verify_only:
        sql_path = sql_file_path or find_default_sql_file()
        logger.info("Target database: %s", database_url.split("@")[-1] if "@" in database_url else database_url)
        execute_sql_file(engine, sql_path)

        if seed_admins:
            seed_admin_users(engine)

        if migrate_images:
            try:
                migrate_external_images_to_bucket(engine, images_dir=images_dir)
            except Exception as e:
                logger.warning("Non-fatal error during image migration: %s", e)

    summary = get_database_summary(engine)
    logger.info("=== Database Verification Summary ===")
    logger.info("Total Objects:    %d (Accepted: %d, Pending: %d)",
                summary["total_objects"], summary["accepted_objects"], summary["pending_objects"])
    logger.info("Total Images:     %d (Bucket: %d, External: %d)",
                summary["total_images"], summary.get("bucket_images", 0), summary.get("external_images", 0))
    logger.info("Total Sources:    %d", summary["total_sources"])
    logger.info("Total Tags:       %d", summary["total_tags"])
    logger.info("Total Image Tags: %d", summary["total_image_tags"])
    logger.info("Total Users:      %d", summary["total_users"])
    for u in summary.get("users", []):
        logger.info("  - User: %s <%s> (admin=%s)", u["username"], u["email"], u["is_admin"])
    logger.info("=====================================")

    return summary


def main():
    parser = argparse.ArgumentParser(description="Seed database with artifacts and initial admin accounts.")
    parser.add_argument(
        "--database-url",
        "-d",
        type=str,
        default=None,
        help="Target database connection URL (defaults to DATABASE_URL env var).",
    )
    parser.add_argument(
        "--sql-file",
        "-f",
        type=Path,
        default=None,
        help="Path to SQL seed file (defaults to data/reduced_dataset/filtered_small.sql).",
    )
    parser.add_argument(
        "--skip-admins",
        action="store_true",
        help="Skip seeding default administrator accounts.",
    )
    parser.add_argument(
        "--skip-images",
        action="store_true",
        help="Skip migrating external images to storage bucket.",
    )
    parser.add_argument(
        "--migrate-images-only",
        action="store_true",
        help="Only run the image migration to bucket without executing SQL seeds.",
    )
    parser.add_argument(
        "--images-dir",
        type=Path,
        default=None,
        help="Path to directory containing local seed images.",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Do not seed data; only query and print existing database statistics.",
    )

    args = parser.parse_args()

    try:
        db_url = resolve_database_url(args.database_url)
        if args.migrate_images_only:
            engine = create_engine(db_url, pool_pre_ping=True)
            migrate_external_images_to_bucket(engine, images_dir=args.images_dir)
            get_database_summary(engine)
            return

        run_seeder(
            database_url=db_url,
            sql_file_path=args.sql_file,
            seed_admins=not args.skip_admins,
            verify_only=args.verify_only,
            migrate_images=not args.skip_images,
            images_dir=args.images_dir,
        )
    except Exception as exc:
        logger.error("Seeding operation failed: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
