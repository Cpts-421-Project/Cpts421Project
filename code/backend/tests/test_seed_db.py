"""
Unit tests for database seeder (seed_db.py).
Tests Normal, Edge, and Extraordinary scenarios using in-memory SQLite and mocks.
Strictly adheres to AAA pattern.
"""

from pathlib import Path
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import sys
import os

# Add backend and backend/src to path
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR / "src"))

from seed_db import (
    resolve_database_url,
    find_default_sql_file,
    execute_sql_file,
    seed_admin_users,
    get_database_summary,
    run_seeder,
)
from src.models import Base, Object, Source, Tag, Image, User


@pytest.fixture
def sqlite_test_engine(tmp_path):
    """Create an isolated SQLite database with Base metadata tables created."""
    engine = create_engine(
        f"sqlite:///{tmp_path}/test_seed.db",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture
def sample_sql_file(tmp_path):
    """Create a sample valid SQL seed file compatible with SQLite syntax."""
    sql_path = tmp_path / "sample_seed.sql"
    sql_content = """
    INSERT INTO sources (citation_text) VALUES ('Met Museum Test Citation');

    INSERT INTO objects (object_type, inventory_number, description, date_display, date_start, date_end, review_status)
    VALUES ('Terracotta Oil Lamp', 'TEST-INV-001', 'Test Lamp description: details', 'c. 300 AD', 200, 400, 'accepted');

    INSERT INTO tags (tag_name) VALUES ('Roman');

    INSERT INTO images (object_id, source_id, image_type, view_type, file_url)
    VALUES (1, 1, 'Photograph', 'Front', 'https://example.com/test-lamp.jpg');

    INSERT INTO image_tags (image_id, tag_id) VALUES (1, 1);
    """
    sql_path.write_text(sql_content, encoding="utf-8")
    return sql_path


# =====================================================================
# 1. Normal Cases (The Happy Path)
# =====================================================================

def test_resolveDatabaseUrl_withPostgresScheme_normalizesToPostgresql():
    # Arrange
    raw_url = "postgres://user:pass@host:5432/dbname"

    # Act
    normalized_url = resolve_database_url(raw_url)

    # Assert
    assert normalized_url == "postgresql://user:pass@host:5432/dbname"


def test_executeSqlFile_validScript_insertsRecords(sqlite_test_engine, sample_sql_file):
    # Arrange
    engine = sqlite_test_engine

    # Act
    execute_sql_file(engine, sample_sql_file)
    summary = get_database_summary(engine)

    # Assert
    assert summary["total_sources"] == 1
    assert summary["total_objects"] == 1
    assert summary["accepted_objects"] == 1
    assert summary["total_images"] == 1
    assert summary["total_tags"] == 1
    assert summary["total_image_tags"] == 1


def test_seedAdminUsers_freshDb_createsAdmins(sqlite_test_engine):
    # Arrange
    engine = sqlite_test_engine

    # Act
    seed_admin_users(engine)
    summary = get_database_summary(engine)

    # Assert
    assert summary["total_users"] == 2
    usernames = [u["username"] for u in summary["users"]]
    assert "halliemeredith" in usernames
    assert "asafKedar" in usernames


# =====================================================================
# 2. Edge Cases (Boundary Conditions & Idempotency)
# =====================================================================

def test_seedAdminUsers_calledTwice_isIdempotent(sqlite_test_engine):
    # Arrange
    engine = sqlite_test_engine
    seed_admin_users(engine)

    # Act: run a second time
    seed_admin_users(engine)
    summary = get_database_summary(engine)

    # Assert: no duplicate admins created
    assert summary["total_users"] == 2


def test_runSeeder_verifyOnly_doesNotMutateDatabase(sqlite_test_engine, sample_sql_file):
    # Arrange
    engine = sqlite_test_engine
    db_url = str(engine.url)

    # Act
    summary = run_seeder(
        database_url=db_url,
        sql_file_path=sample_sql_file,
        seed_admins=True,
        verify_only=True,
    )

    # Assert: verify_only should see 0 records because seeding was skipped
    assert summary["total_objects"] == 0
    assert summary["total_users"] == 0


def test_findDefaultSqlFile_returnsExistingOrResolvedPath():
    # Act
    path = find_default_sql_file()

    # Assert
    assert path is not None
    assert isinstance(path, Path)
    assert path.name == "filtered_small.sql"


# =====================================================================
# 3. Extraordinary Cases (Sad Path & Fault Handling)
# =====================================================================

def test_executeSqlFile_nonExistentPath_throwsFileNotFoundError(sqlite_test_engine, tmp_path):
    # Arrange
    missing_file = tmp_path / "does_not_exist.sql"

    # Act & Assert
    with pytest.raises(FileNotFoundError):
        execute_sql_file(sqlite_test_engine, missing_file)


def test_resolveDatabaseUrl_noEnvOrParam_throwsValueError(monkeypatch):
    # Arrange: clear DATABASE_URL and mock non-existent .env
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr(Path, "is_file", lambda self: False)

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        resolve_database_url(None)
    assert "Database URL not found" in str(exc_info.value)


def test_executeSqlFile_invalidSqlSyntax_rollsBackAndThrows(sqlite_test_engine, tmp_path):
    # Arrange
    invalid_sql = tmp_path / "bad.sql"
    invalid_sql.write_text("THIS IS NOT VALID SQL STATEMENT;", encoding="utf-8")

    # Act & Assert
    with pytest.raises(Exception):
        execute_sql_file(sqlite_test_engine, invalid_sql)
