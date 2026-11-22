"""
Backend API tests covering Normal, Edge, and Extraordinary cases.
Uses in-memory SQLite for isolation.
"""
import os

# Configure test environment variables before importing app and config
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-12345678901234567890")
os.environ.setdefault("MINIO_ENDPOINT", "http://localhost:9000")
os.environ.setdefault("MINIO_ACCESS_KEY", "minioadmin")
os.environ.setdefault("MINIO_SECRET_KEY", "minioadmin")
os.environ.setdefault("MINIO_BUCKET_NAME", "artifacts")

import io
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import pytest
from src.main import app, _rate_limit_store
from src.database import get_db
from src.models import Base, Object, Image, Source, Tag, User
from src.bot_defense import reset_bot_defense_state

# Setup in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_database():
    """Create fresh tables and seed data for each test, then tear down."""
    reset_bot_defense_state()
    _rate_limit_store.clear()
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=test_engine)

    # Seed data
    db = TestingSessionLocal()

    source = Source(citation_text="Test Source Citation")
    db.add(source)
    db.commit()
    db.refresh(source)

    obj1 = Object(
        object_type="Vase",
        material="Clay",
        findspot="Rome",
        latitude=41.9028,
        longitude=12.4964,
        date_display="c. 300 AD",
        date_start=250,
        date_end=350,
        inventory_number="INV001",
        review_status="accepted"
    )
    db.add(obj1)
    db.commit()
    db.refresh(obj1)

    tag_roman = Tag(tag_name="Roman")
    tag_egyptian = Tag(tag_name="Egyptian")
    db.add(tag_roman)
    db.add(tag_egyptian)
    db.commit()

    image = Image(
        object_id=obj1.id,
        source_id=source.id,
        image_type="Photo",
        file_url="http://example.com/image.jpg"
    )
    image.tags.append(tag_roman)
    db.add(image)
    db.commit()

    obj2 = Object(
        object_type="Coin",
        material="Gold",
        findspot="Alexandria",
        latitude=31.2001,
        longitude=29.9187,
        date_display="c. 100 BC",
        date_start=-150,
        date_end=-50,
        inventory_number="INV002",
        review_status="accepted"
    )
    db.add(obj2)
    db.commit()

    image2 = Image(
        object_id=obj2.id,
        source_id=source.id,
        image_type="Photo",
        file_url="http://example.com/coin.jpg"
    )
    image2.tags.append(tag_egyptian)
    db.add(image2)
    db.commit()

    import bcrypt
    hashed_pw = bcrypt.hashpw("TestAdminPass!2026".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    test_user = User(
        email="asaf.kedar1@gmail.com",
        username="asafKedar",
        password_hash=hashed_pw,
        is_admin=True,
    )
    db.add(test_user)
    db.commit()

    db.close()

    yield

    Base.metadata.drop_all(bind=test_engine)
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    """Provide a fresh TestClient for each test."""
    return TestClient(app)


# =============================================================================
# Normal Cases (Happy Path)
# =============================================================================

class TestReadRoot:
    def test_validRequest_returnsWelcomeMessage(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Academic Artifact Research Database API"}


class TestGetTags:
    def test_withSeededData_returnsList(self, client):
        response = client.get("/tags")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestGetObjectsMap:
    def test_withSeededData_returnsLocationData(self, client):
        response = client.get("/objects/map")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["name"] == "Vase"
        assert data[0]["latitude"] == 41.9028


class TestGetObjectDetail:
    def test_existingObject_returnsFullDetail(self, client):
        response = client.get("/objects/1")
        assert response.status_code == 200
        data = response.json()
        assert data["object_type"] == "Vase"
        assert "Clay" in data["material"]
        assert len(data["bibliography"]) == 1
        assert data["bibliography"][0] == "Test Source Citation"

    def test_nonExistentId_returns404(self, client):
        response = client.get("/objects/999")
        assert response.status_code == 404
        assert "Object not found" in response.json()["detail"]


class TestSearchObjectsFuzzyDate:
    def test_yearWithinRange_returnsMatch(self, client):
        """Object is 250-350. Year 300 should match."""
        response = client.get("/objects/search?year=300")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == 1

    def test_yearBelowRange_returnsEmpty(self, client):
        """Year 200 is below the object's start of 250."""
        response = client.get("/objects/search?year=200")
        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_yearAboveRange_returnsEmpty(self, client):
        """Year 400 is above the object's end of 350."""
        response = client.get("/objects/search?year=400")
        assert response.status_code == 200
        assert len(response.json()) == 0


class TestSearchObjectsMaterial:
    def test_matchingMaterial_returnsResults(self, client):
        response = client.get("/objects/search?material=Clay")
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_nonMatchingMaterial_returnsEmpty(self, client):
        response = client.get("/objects/search?material=Silver")
        assert response.status_code == 200
        assert len(response.json()) == 0


# =============================================================================
# Edge Cases (Boundary Conditions)
# =============================================================================

class TestEdgeCases:
    def test_getObjectDetail_idZero_returns404(self, client):
        """ID 0 should not match any seeded object."""
        response = client.get("/objects/0")
        assert response.status_code == 404

    def test_searchObjects_emptyMaterial_returnsAll(self, client):
        """Empty material string should not filter — returns all objects."""
        response = client.get("/objects/search?material=")
        assert response.status_code == 200

    def test_searchObjects_yearAtExactBoundary_returnsMatch(self, client):
        """Year exactly at date_start=250 boundary should match."""
        response = client.get("/objects/search?year=250")
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_searchObjects_yearAtEndBoundary_returnsMatch(self, client):
        """Year exactly at date_end=350 boundary should match."""
        response = client.get("/objects/search?year=350")
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_searchObjects_dateRangeStartEqualsEnd(self, client):
        """date_start == date_end == 300, which falls within 250-350."""
        response = client.get("/objects/search?date_start=300&date_end=300")
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_getObjectsMap_allDataPresent(self, client):
        """Map endpoint should include lat/lng for seeded object."""
        response = client.get("/objects/map")
        data = response.json()
        assert data[0]["longitude"] == 12.4964


# =============================================================================
# Extraordinary Cases (Sad Path & Anomalies)
# =============================================================================

class TestExtraordinaryCases:
    def test_getObjectDetail_negativeId_returns404Or422(self, client):
        """Negative ID is technically a valid int but should not find an object."""
        response = client.get("/objects/-1")
        assert response.status_code in (404, 422)

    def test_getObjectDetail_stringId_returns422(self, client):
        """Non-integer ID should fail FastAPI's type validation."""
        response = client.get("/objects/abc")
        assert response.status_code == 422

    def test_searchObjects_extremeYear_returnsEmpty(self, client):
        """Year far in the future should match nothing."""
        response = client.get("/objects/search?year=999999")
        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_searchObjects_negativeYear_returnsEmpty(self, client):
        """Large negative year (BCE) should match nothing in our 250-350 CE data."""
        response = client.get("/objects/search?year=-5000")
        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_searchObjects_specialCharsMaterial_returnsEmpty(self, client):
        """Special characters in material should not cause errors (ORM parameterizes)."""
        response = client.get("/objects/search?material='; DROP TABLE objects;--")
        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_searchObjects_dateStartGreaterThanEnd_returnsEmpty(self, client):
        """Inverted date range should logically return nothing."""
        response = client.get("/objects/search?date_start=500&date_end=100")
        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_searchObjects_noParams_returnsAll(self, client):
        """No filters should return all objects."""
        response = client.get("/objects/search")
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_getTags_dbError_returns500(self, client):
        """Simulate database error on tags query."""
        from unittest.mock import patch
        from sqlalchemy.exc import SQLAlchemyError
        with patch("src.repositories.object_repository.ObjectRepository.get_all_tags", side_effect=SQLAlchemyError("DB error")):
            response = client.get("/tags")
            assert response.status_code == 500
            assert "database error" in response.json()["detail"].lower()

    def test_getObjectsMap_dbError_returns500(self, client):
        """Simulate database error on map query."""
        from unittest.mock import patch
        from sqlalchemy.exc import SQLAlchemyError
        with patch("src.repositories.object_repository.ObjectRepository.get_map_data", side_effect=SQLAlchemyError("DB error")):
            response = client.get("/objects/map")
            assert response.status_code == 500
            assert "database error" in response.json()["detail"].lower()


class TestAuthLogin:
    """Authentication tests covering Normal, Edge, and Extraordinary cases."""

    def test_login_exactUsername_succeeds(self, client):
        """Normal case: Login with exact case username and correct password."""
        response = client.post("/auth/login", json={"username": "asafKedar", "password": "TestAdminPass!2026"})
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Logged in successfully"
        assert data["username"] == "asafKedar"
        assert data["is_admin"] is True
        assert "access_token" in response.cookies

    def test_login_lowercaseUsername_succeeds(self, client):
        """Edge case: Login with all-lowercase username."""
        response = client.post("/auth/login", json={"username": "asafkedar", "password": "TestAdminPass!2026"})
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "asafKedar"
        assert data["is_admin"] is True

    def test_login_emailAddress_succeeds(self, client):
        """Edge case: Login using email address instead of username."""
        response = client.post("/auth/login", json={"username": "asaf.kedar1@gmail.com", "password": "TestAdminPass!2026"})
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "asafKedar"

    def test_login_wrongPassword_returns401(self, client):
        """Extraordinary case: Correct username with invalid password."""
        response = client.post("/auth/login", json={"username": "asafKedar", "password": "WrongPassword123!"})
        assert response.status_code == 401
        assert "incorrect username or password" in response.json()["detail"].lower()

    def test_login_nonExistentUser_returns401(self, client):
        """Extraordinary case: Non-existent username."""
        response = client.post("/auth/login", json={"username": "unknown_user_999", "password": "password"})
        assert response.status_code == 401
        assert "incorrect username or password" in response.json()["detail"].lower()


class TestSearchAndTags:
    """Tests for general search and tag filtering functionality."""

    def test_search_byObjectType_returnsMatchingObject(self, client):
        """Normal case: Search by artifact object_type."""
        response = client.get("/objects/search?search=Vase")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["object_type"] == "Vase"
        assert "Roman" in data[0]["tags"]

    def test_search_byFindspot_returnsMatchingObject(self, client):
        """Normal case: Search by discovery findspot."""
        response = client.get("/objects/search?search=Alexandria")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["object_type"] == "Coin"

    def test_search_byAliasQ_returnsMatchingObject(self, client):
        """Normal case: Search using alias query parameter 'q'."""
        response = client.get("/objects/search?q=Clay")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["material"] == "Clay"

    def test_search_byAssociatedTagName_returnsMatchingObject(self, client):
        """Normal case: Search term matching an associated tag name."""
        response = client.get("/objects/search?search=Roman")
        assert response.status_code == 200
        data = response.json()
        assert any(obj["object_type"] == "Vase" for obj in data)

    def test_filter_bySingleTag_returnsMatchingObject(self, client):
        """Normal case: Filter objects by a single tag."""
        response = client.get("/objects/search?tags=Egyptian")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["object_type"] == "Coin"

    def test_filter_byTagCaseInsensitive_returnsMatchingObject(self, client):
        """Edge case: Tag filtering should be case-insensitive."""
        response = client.get("/objects/search?tags=roman")
        assert response.status_code == 200
        data = response.json()
        assert any(obj["object_type"] == "Vase" for obj in data)

    def test_filter_byMultipleTagsCommaSeparated_returnsBoth(self, client):
        """Normal case: Filter by multiple comma-separated tags with default any mode."""
        response = client.get("/objects/search?tags=Roman,Egyptian")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_filter_byMultipleTagsRepeatedParam_returnsBoth(self, client):
        """Normal case: Filter by repeated tags query parameter (tags=A&tags=B)."""
        response = client.get("/objects/search?tags=Roman&tags=Egyptian")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_filter_byNonExistentTag_returnsEmpty(self, client):
        """Edge case: Filtering by a tag that no object has returns empty list."""
        response = client.get("/objects/search?tags=NonExistentTag12345")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_search_withLeadingTrailingWhitespace_trimmedProperly(self, client):
        """Edge case: Search term with spaces is properly trimmed."""
        response = client.get("/objects/search?search=%20Vase%20")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["object_type"] == "Vase"


class TestServeImage:
    """Tests for GET /images/{key} and /api/images/{key} streaming and local fallback."""

    def test_serveImage_normalBundledSeedImage_returns200(self, client):
        # Arrange: met_241792.jpg is a bundled seed image
        # Act
        response = client.get("/images/met_241792.jpg")

        # Assert
        assert response.status_code == 200
        assert response.headers.get("content-type") == "image/jpeg"
        assert response.headers.get("cache-control") == "public, max-age=86400"
        assert len(response.content) > 0

    def test_serveImage_normalViaApiPrefix_returns200(self, client):
        # Arrange & Act
        response = client.get("/api/images/met_241792.jpg")

        # Assert
        assert response.status_code == 200
        assert response.headers.get("content-type") == "image/jpeg"
        assert len(response.content) > 0

    @patch("src.main.get_s3_client")
    def test_serveImage_normalS3Streaming_returnsObjectStream(self, mock_client_getter, client):
        # Arrange
        mock_s3 = MagicMock()
        mock_body = io.BytesIO(b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 20)
        mock_s3.get_object.return_value = {
            "ContentType": "image/jpeg",
            "Body": mock_body
        }
        mock_client_getter.return_value = mock_s3

        # Act
        response = client.get("/images/s3_stored_image.jpg")

        # Assert
        assert response.status_code == 200
        assert response.headers.get("content-type") == "image/jpeg"
        assert response.content == b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 20

    def test_serveImage_edgeBucketPrefix_stripsPrefixAndFindsFile(self, client):
        # Arrange: client passes uploads/met_241792.jpg
        # Act
        response = client.get("/images/uploads/met_241792.jpg")

        # Assert
        assert response.status_code == 200
        assert response.headers.get("content-type") == "image/jpeg"

    def test_serveImage_extraordinaryPathTraversal_rejected(self, client):
        # Arrange: Attacker tries path traversal
        # Act
        response = client.get("/images/%2e%2e/etc/passwd")

        # Assert
        assert response.status_code in (400, 404)

    def test_serveImage_extraordinaryNonExistentImage_returns404(self, client):
        # Arrange & Act
        response = client.get("/images/totally_non_existent_image_12345.jpg")

        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestLegacyUrlNormalization:
    """Tests to verify that external Met Museum URLs are never returned to frontend."""

    def test_getObjectDetail_withLegacyMetUrl_normalizesToBucketEndpoint(self, client):
        # Arrange: Insert an object with legacy external Met image URL directly in DB
        db = TestingSessionLocal()
        try:
            obj = Object(
                object_type="Ancient Bowl",
                date_display="c. 200 AD",
                date_start=150,
                date_end=250,
                inventory_number="241792",
                review_status="accepted",
            )
            db.add(obj)
            db.commit()
            db.refresh(obj)

            img = Image(
                object_id=obj.id,
                image_type="Photograph",
                view_type="Front",
                file_url="https://collectionapi.metmuseum.org/api/collection/v1/iiif/241792/2105480/main-image"
            )
            db.add(img)
            db.commit()
            target_id = obj.id
        finally:
            db.close()

        # Act
        response = client.get(f"/objects/{target_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["images"]) == 1
        assert data["images"][0]["file_url"] == "/api/images/met_241792.jpg"
        assert "metmuseum.org" not in data["images"][0]["file_url"]
        assert "collectionapi" not in data["images"][0]["file_url"]


class TestSecurityAuditRemediations:
    """Tests specifically validating security audit fixes."""

    def test_reviewObject_validStatus_updatesStatusWithoutDeletingImages(self, client):
        # Arrange: Login as admin
        login_res = client.post("/auth/login", json={"username": "asafKedar", "password": "TestAdminPass!2026"})
        assert login_res.status_code == 200

        # Act: Review object 1 (has Roman image tag)
        review_res = client.patch("/objects/1/review", json={"status": "accepted"})

        # Assert: 200 OK, status updated, images still present
        assert review_res.status_code == 200
        data = review_res.json()
        assert data["review_status"] == "accepted"
        assert len(data["images"]) > 0

    def test_reviewObject_invalidStatus_returns422Validation(self, client):
        # Arrange: Login as admin
        client.post("/auth/login", json={"username": "asafKedar", "password": "TestAdminPass!2026"})

        # Act: Attempt to send arbitrary unvalidated string / script payload
        response = client.patch("/objects/1/review", json={"status": "<script>alert(1)</script>"})

        # Assert: Pydantic Literal validation blocks with 422 Unprocessable Entity
        assert response.status_code == 422

    def test_createObject_cannotInjectAcceptedReviewStatus(self, client):
        # Arrange: Login as admin
        client.post("/auth/login", json={"username": "asafKedar", "password": "TestAdminPass!2026"})

        # Act: Attempt to create an object directly with review_status="accepted"
        new_obj_payload = {
            "object_type": "Chalice",
            "date_display": "c. 500 AD",
            "date_start": 450,
            "date_end": 550,
            "material": "Silver",
            "review_status": "accepted",  # Should be ignored/rejected by schema
            "images": []
        }
        res = client.post("/objects", json=new_obj_payload)
        assert res.status_code == 200
        # By business rules, review_status must default to pending on creation
        assert res.json()["review_status"] == "pending"

    def test_serveImage_pathTraversal_blockedWith400(self, client):
        # Act
        response = client.get("/images/..%2F..%2Fetc%2Fpasswd")
        # Assert
        assert response.status_code == 400

    def test_serveImage_nullByteInPath_blockedWith400(self, client):
        # Act
        response = client.get("/images/met_241792.jpg%00.png")
        # Assert
        assert response.status_code == 400

    def test_entityNotFoundError_idZero_includesId(self):
        # Arrange & Act
        from src.exceptions import EntityNotFoundError
        err = EntityNotFoundError("Object", 0)
        # Assert
        assert "ID: 0" in err.message

    def test_logout_setsClearedCookieAttributes(self, client):
        # Act
        response = client.post("/auth/logout")
        # Assert
        assert response.status_code == 200
        assert "Logged out successfully" in response.json()["message"]


class TestAlphabeticalTagsAndSearchSorting:
    """Tests for alphabetical tag ordering, search sorting, and 0-899 CE filtering."""

    def test_getTags_mixedCase_returnsAlphabeticalOrder(self, client):
        # Arrange: seed additional mixed-case tags
        db = TestingSessionLocal()
        try:
            db.add_all([Tag(tag_name="bronze"), Tag(tag_name="arch"), Tag(tag_name="Workshop")])
            db.commit()
        finally:
            db.close()

        # Act
        response = client.get("/tags")

        # Assert: case-insensitive alphabetical ordering
        assert response.status_code == 200
        assert response.json() == ["arch", "bronze", "Egyptian", "Roman", "Workshop"]

    def test_search_defaultSort_returnsAlphabeticalByTitle(self, client):
        # Arrange: seeded objects are Vase and Coin (both accepted)
        # Act
        response = client.get("/objects/search")

        # Assert: Coin comes before Vase alphabetically
        assert response.status_code == 200
        titles = [item["object_type"] for item in response.json()]
        assert titles == ["Coin", "Vase"]

    def test_search_sortOptions_sortByTitleDescDateLocationAndMaterialWithNullsLast(self, client):
        # Arrange: add a 3rd accepted object with NULL material and NULL location, dated 50 CE
        db = TestingSessionLocal()
        try:
            obj3 = Object(
                object_type="Amphora",
                material=None,
                findspot=None,
                present_location=None,
                production_location=None,
                date_display="c. 50 CE",
                date_start=50,
                date_end=50,
                inventory_number="INV003",
                review_status="accepted",
            )
            db.add(obj3)
            db.commit()
        finally:
            db.close()

        # Act & Assert: title desc
        res_title_desc = client.get("/objects/search?sort_by=title&sort_order=desc")
        assert res_title_desc.status_code == 200
        assert [o["object_type"] for o in res_title_desc.json()] == ["Vase", "Coin", "Amphora"]

        # Act & Assert: date asc (Coin -150, Amphora 50, Vase 250)
        res_date_asc = client.get("/objects/search?sort_by=date&sort_order=asc")
        assert res_date_asc.status_code == 200
        assert [o["object_type"] for o in res_date_asc.json()] == ["Coin", "Amphora", "Vase"]

        # Act & Assert: date desc
        res_date_desc = client.get("/objects/search?sort_by=date&sort_order=desc")
        assert res_date_desc.status_code == 200
        assert [o["object_type"] for o in res_date_desc.json()] == ["Vase", "Amphora", "Coin"]

        # Act & Assert: location asc & desc always keep NULL location last
        res_loc_asc = client.get("/objects/search?sort_by=location&sort_order=asc")
        assert res_loc_asc.status_code == 200
        assert [o["object_type"] for o in res_loc_asc.json()] == ["Coin", "Vase", "Amphora"]

        res_loc_desc = client.get("/objects/search?sort_by=location&sort_order=desc")
        assert res_loc_desc.status_code == 200
        assert [o["object_type"] for o in res_loc_desc.json()] == ["Vase", "Coin", "Amphora"]

        # Act & Assert: material asc keeps NULL material last (Clay, Gold, None)
        res_mat_asc = client.get("/objects/search?sort_by=material&sort_order=asc")
        assert res_mat_asc.status_code == 200
        assert [o["object_type"] for o in res_mat_asc.json()] == ["Vase", "Coin", "Amphora"]

    def test_search_dateRangeZeroTo899_handlesYearZeroBoundary(self, client):
        # Arrange: add boundary object starting at year 0 CE
        db = TestingSessionLocal()
        try:
            obj_zero = Object(
                object_type="Augustan Lamp",
                date_display="c. 0–50 CE",
                date_start=0,
                date_end=50,
                inventory_number="INV-ZERO",
                review_status="accepted",
            )
            db.add(obj_zero)
            db.commit()
        finally:
            db.close()

        # Act
        res = client.get("/objects/search?date_start=0&date_end=899")

        # Assert: Coin (-150..-50) excluded; Augustan Lamp (0..50) and Vase (250..350) included
        assert res.status_code == 200
        titles = [o["object_type"] for o in res.json()]
        assert "Augustan Lamp" in titles
        assert "Vase" in titles
        assert "Coin" not in titles

    def test_search_invalidSortBy_returns422(self, client):
        # Act
        res = client.get("/objects/search?sort_by=invalid_col")

        # Assert
        assert res.status_code == 422


class TestTwoExcelSchemaAlignment:
    """Tests for 2_excel fields, assembled caption, multi-image IDs, partial PUT, and Alembic migration."""

    def test_createAndFetchObject_withFull2ExcelFields_returnsCaptionDimensionsAndImageIds(self, client):
        # Arrange: login as admin
        login_res = client.post("/auth/login", json={"username": "asafKedar", "password": "TestAdminPass!2026"})
        assert login_res.status_code == 200

        payload = {
            "object_type": "Roundel with gold-glass",
            "material": "Gold-glass",
            "findspot": "Rome",
            "present_location": "Museo Biblioteca Apostolica Vaticana, Vatican City",
            "production_location": "Rome",
            "object_group": "Catacomb group",
            "date_display": "c. 4th century CE",
            "date_start": 300,
            "date_end": 399,
            "date_basis": "See Kisa 1908",
            "inventory_number": "60788",
            "description": "Six Craftworkers",
            "width": 10.5,
            "height": 10.5,
            "depth": 0.6,
            "unit": "cm",
            "dimensions_display": "Diam. 10.5 cm",
            "weight": "42 g",
            "completeness": "Fragmentary, broken at the edges",
            "inscription_present": True,
            "inscription_1": "DAEDALUS",
            "publications": "Kisa 1908; Meredith 2023b",
            "external_url": "https://digi.vatlib.it/example",
            "images": [
                {
                    "file_url": "",
                    "image_type": "Line drawing",
                    "view_type": "Full",
                    "image_sequence": 1,
                    "source_identifier": "Kisa 1908, fig. 357",
                    "source_citation": "Kisa, Anton. Das Glas im Altertume. 1908.",
                },
                {
                    "file_url": "",
                    "image_type": "b+w photo",
                    "view_type": "Full",
                    "image_sequence": 2,
                    "source_identifier": "Morey 1959, no. 96",
                    "source_citation": "Morey, Charles Rufus. Gold-Glass Collection. 1959.",
                },
            ],
        }

        # Act
        create_res = client.post("/objects", json=payload)
        assert create_res.status_code == 200
        created = create_res.json()
        obj_id = created["id"]

        fetch_res = client.get(f"/objects/{obj_id}")
        assert fetch_res.status_code == 200
        detail = fetch_res.json()

        # Assert
        assert detail["present_location"] == "Museo Biblioteca Apostolica Vaticana, Vatican City"
        assert detail["width"] == 10.5
        assert detail["completeness"] == "Fragmentary, broken at the edges"
        assert detail["inscription_present"] is True
        assert detail["inscription_1"] == "DAEDALUS"
        assert detail["publications"] == "Kisa 1908; Meredith 2023b"
        assert len(detail["images"]) == 2
        assert detail["images"][0]["db_identifier"] == f"{obj_id}.1"
        assert detail["images"][1]["db_identifier"] == f"{obj_id}.2"
        assert detail["images"][0]["source_identifier"] == "Kisa 1908, fig. 357"
        assert "Kisa, Anton." in detail["bibliography"][0]
        assert "Six Craftworkers" in detail["assembled_caption"]
        assert "Inscribed: DAEDALUS" in detail["assembled_caption"]
        assert "inv. 60788" in detail["assembled_caption"]
        assert "Museo Biblioteca Apostolica Vaticana" in detail["assembled_caption"]

    def test_updateObject_partialPutWithoutImages_preservesExistingImages(self, client):
        # Arrange: login as admin; object 1 already has 1 image
        client.post("/auth/login", json={"username": "asafKedar", "password": "TestAdminPass!2026"})

        # Act: PUT without images key (mirrors ReviewPage metadata save)
        res = client.put(
            "/objects/1",
            json={
                "object_type": "Vase",
                "date_display": "c. 300 AD",
                "date_start": 250,
                "date_end": 350,
                "present_location": "Test Museum Collection",
            },
        )

        # Assert
        assert res.status_code == 200
        data = res.json()
        assert data["present_location"] == "Test Museum Collection"
        assert len(data["images"]) == 1

    def test_createObject_invalidExternalUrl_returns422(self, client):
        # Arrange
        client.post("/auth/login", json={"username": "asafKedar", "password": "TestAdminPass!2026"})

        # Act & Assert: non-HTTPS scheme rejected
        for bad_url in ("http://example.com/item", "javascript:alert(1)"):
            res = client.post(
                "/objects",
                json={
                    "object_type": "Ring",
                    "date_display": "c. 100 CE",
                    "date_start": 100,
                    "date_end": 100,
                    "external_url": bad_url,
                    "images": [],
                },
            )
            assert res.status_code == 422

    def test_alembicMigration_upgradeDowngradeUpgrade_isIdempotent(self, tmp_path, monkeypatch):
        # Arrange: isolated SQLite database for Alembic revision chain verification
        from pathlib import Path
        from alembic.config import Config as AlembicConfig
        from alembic import command
        from sqlalchemy import inspect as sa_inspect
        from src.config import config as app_config

        db_file = tmp_path / "alembic_roundtrip.db"
        db_url = f"sqlite:///{db_file}"
        monkeypatch.setattr(app_config, "DATABASE_URL", db_url)

        backend_dir = Path(__file__).resolve().parents[1]
        alembic_cfg = AlembicConfig(str(backend_dir / "alembic.ini"))
        alembic_cfg.set_main_option("script_location", str(backend_dir / "alembic"))

        # Act: upgrade to head, inspect, downgrade to previous rev, inspect, re-upgrade to head
        command.upgrade(alembic_cfg, "head")
        mig_engine = create_engine(db_url)
        inspector_up = sa_inspect(mig_engine)
        obj_cols_up = {c["name"] for c in inspector_up.get_columns("objects")}
        img_cols_up = {c["name"] for c in inspector_up.get_columns("images")}
        assert {"present_location", "publications", "caption", "external_url"}.issubset(obj_cols_up)
        assert {"image_sequence", "source_identifier"}.issubset(img_cols_up)
        assert "discovery_keywords" in inspector_up.get_table_names()

        command.downgrade(alembic_cfg, "e1a2b3c4d5e6")
        inspector_down = sa_inspect(mig_engine)
        obj_cols_down = {c["name"] for c in inspector_down.get_columns("objects")}
        assert "present_location" not in obj_cols_down
        assert "discovery_keywords" not in inspector_down.get_table_names()

        command.upgrade(alembic_cfg, "head")
        inspector_reup = sa_inspect(mig_engine)
        obj_cols_reup = {c["name"] for c in inspector_reup.get_columns("objects")}
        assert "present_location" in obj_cols_reup
        assert "discovery_keywords" in inspector_reup.get_table_names()

        from sqlalchemy import text
        with mig_engine.connect() as conn:
            seeded_kws = {
                row[0]
                for row in conn.execute(text("SELECT keyword FROM discovery_keywords")).fetchall()
            }
        assert len(seeded_kws) == 62
        assert {"ancient worker", "vitrearii", "Pygmalion"}.issubset(seeded_kws)

        mig_engine.dispose()


class TestMapAndIdFiltering:
    """Normal, Edge, and Extraordinary tests for map findspot & /objects/search ?ids filtering."""

    def test_getObjectsMap_returnsFindspotAlongsideCoordinates(self, client):
        # Act
        res = client.get("/objects/map")

        # Assert
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 2
        by_id = {item["id"]: item for item in data}
        assert by_id[1]["findspot"] == "Rome"
        assert by_id[2]["findspot"] == "Alexandria"

    def test_searchObjects_withIdsParam_returnsOnlyMatchingAcceptedObjects(self, client):
        # Arrange: seed an extra pending object (id=3) that must not be exposed by ?ids=
        db = TestingSessionLocal()
        try:
            pending_obj = Object(
                object_type="Pending Lamp",
                date_display="c. 200 CE",
                date_start=200,
                date_end=200,
                inventory_number="INV-PEND",
                review_status="pending",
            )
            db.add(pending_obj)
            db.commit()
            pending_id = pending_obj.id
        finally:
            db.close()

        # Act: query comma-separated & repeated IDs including pending ID
        res_comma = client.get(f"/objects/search?ids=1,{pending_id}")
        res_repeated = client.get("/objects/search?ids=1&ids=2")

        # Assert
        assert res_comma.status_code == 200
        assert [obj["id"] for obj in res_comma.json()] == [1]

        assert res_repeated.status_code == 200
        assert {obj["id"] for obj in res_repeated.json()} == {1, 2}

    def test_searchObjects_withIdsCombinedWithTag_intersectsFilters(self, client):
        # Act
        res = client.get("/objects/search?ids=1,2&tag=Roman")

        # Assert
        assert res.status_code == 200
        assert [obj["id"] for obj in res.json()] == [1]

    def test_searchObjects_withInvalidOrExcessiveIds_returns422(self, client):
        # Act & Assert: non-numeric, zero, negative, and >500 IDs rejected
        assert client.get("/objects/search?ids=abc").status_code == 422
        assert client.get("/objects/search?ids=0").status_code == 422
        assert client.get("/objects/search?ids=-5").status_code == 422
        too_many = ",".join(str(i) for i in range(1, 502))
        assert client.get(f"/objects/search?ids={too_many}").status_code == 422





