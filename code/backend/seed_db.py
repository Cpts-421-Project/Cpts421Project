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


def get_database_summary(engine: Engine) -> Dict[str, Any]:
    """Retrieve row counts across key tables for verification."""
    backend_src = str(Path(__file__).resolve().parent / "src")
    if backend_src not in sys.path:
        sys.path.insert(0, backend_src)

    from src.models import Object, Image, Source, Tag, User, image_tags

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
) -> Dict[str, Any]:
    """Main seeder orchestration function."""
    engine = create_engine(database_url, pool_pre_ping=True)

    if not verify_only:
        sql_path = sql_file_path or find_default_sql_file()
        logger.info("Target database: %s", database_url.split("@")[-1] if "@" in database_url else database_url)
        execute_sql_file(engine, sql_path)

        if seed_admins:
            seed_admin_users(engine)

    summary = get_database_summary(engine)
    logger.info("=== Database Verification Summary ===")
    logger.info("Total Objects:    %d (Accepted: %d, Pending: %d)",
                summary["total_objects"], summary["accepted_objects"], summary["pending_objects"])
    logger.info("Total Images:     %d", summary["total_images"])
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
        "--verify-only",
        action="store_true",
        help="Do not seed data; only query and print existing database statistics.",
    )

    args = parser.parse_args()

    try:
        db_url = resolve_database_url(args.database_url)
        run_seeder(
            database_url=db_url,
            sql_file_path=args.sql_file,
            seed_admins=not args.skip_admins,
            verify_only=args.verify_only,
        )
    except Exception as exc:
        logger.error("Seeding operation failed: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
