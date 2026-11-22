"""
Tests for admin predefined museum discovery & duplicate-safe import pipeline.
Covers Normal, Edge, and Extraordinary cases following AAA pattern with mocked HTTP & S3.
"""
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-12345678901234567890")
os.environ.setdefault("MINIO_ENDPOINT", "http://localhost:9000")
os.environ.setdefault("MINIO_ACCESS_KEY", "minioadmin")
os.environ.setdefault("MINIO_SECRET_KEY", "minioadmin")
os.environ.setdefault("MINIO_BUCKET_NAME", "artifacts")

from unittest.mock import MagicMock, patch
import pytest
import requests
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.main import app
from src.database import get_db
from src.models import Base, Object, Image, Source, Tag, User
from src.bot_defense import reset_bot_defense_state

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
    """Create isolated schema, seed admin user and existing objects for dedup testing."""
    reset_bot_defense_state()
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=test_engine)

    db = TestingSessionLocal()
    try:
        existing_met = Object(
            object_type="Terracotta oil lamp",
            present_location="The Metropolitan Museum of Art, New York",
            findspot="Cyprus",
            date_display="c. 200 CE",
            date_start=200,
            date_end=200,
            inventory_number="241792",
            external_url="https://www.metmuseum.org/art/collection/search/241792",
            review_status="accepted",
        )
        existing_cma = Object(
            object_type="Ribbed Glass Bowl",
            present_location="The Cleveland Museum of Art, Cleveland",
            date_display="1–100 CE",
            date_start=1,
            date_end=100,
            inventory_number="2009.474",
            external_url="https://clevelandart.org/art/2009.474",
            review_status="accepted",
        )
        db.add_all([existing_met, existing_cma])

        import bcrypt
        hashed_pw = bcrypt.hashpw("TestAdminPass!2026".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        admin = User(
            email="asaf.kedar1@gmail.com",
            username="asafKedar",
            password_hash=hashed_pw,
            is_admin=True,
        )
        db.add(admin)
        db.commit()
    finally:
        db.close()

    yield

    Base.metadata.drop_all(bind=test_engine)
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    return TestClient(app)


def _login_admin(client: TestClient) -> None:
    res = client.post("/auth/login", json={"username": "asafKedar", "password": "TestAdminPass!2026"})
    assert res.status_code == 200


def _mock_response(payload: dict, status_code: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = payload
    if status_code >= 400:
        resp.raise_for_status.side_effect = requests.HTTPError(f"HTTP {status_code}")
    else:
        resp.raise_for_status.return_value = None
    return resp


class TestDiscoveryAuthAndCatalog:
    """Normal and authorization checks for /admin/discovery/* endpoints."""

    def test_discoveryEndpoints_unauthenticated_return401(self, client):
        # Act & Assert
        assert client.get("/admin/discovery/museums").status_code == 401
        assert client.post("/admin/discovery/search", json={
            "museums": ["met"], "keywords": ["glass"], "date_start": 0, "date_end": 899, "limit_per_museum": 5
        }).status_code == 401
        assert client.post("/admin/discovery/import", json={"candidates": []}).status_code in (401, 422)

    def test_listMuseums_authenticatedAdmin_returnsFourPredefinedMuseums(self, client):
        # Arrange
        _login_admin(client)

        # Act
        res = client.get("/admin/discovery/museums")

        # Assert
        assert res.status_code == 200
        museums = res.json()
        assert [m["id"] for m in museums] == ["met", "cma", "aic", "vam"]
        for m in museums:
            assert m["default_date_start"] == 0
            assert m["default_date_end"] == 899
            assert len(m["default_keywords"]) >= 1


class TestMuseumAdaptersAndFullFields:
    """Verify full 2_excel field mapping & deduplication across all 4 museum adapters."""

    @patch("src.services.museum_discovery_service.requests.post")
    @patch("src.services.museum_discovery_service.requests.get")
    def test_search_allFourMuseums_extractsFullMetadataAndSkipsDuplicates(self, mock_get, mock_post, client):
        # Arrange
        _login_admin(client)

        def fake_get(url, params=None, headers=None, timeout=10):
            if "collectionapi.metmuseum.org/public/collection/v1.1/search" in url:
                # 241792 already exists in DB (should be skipped before detail fetch!)
                return _mock_response({"total": 2, "objectIDs": [241792, 555001]})
            if url.endswith("/objects/555001"):
                return _mock_response({
                    "objectID": 555001,
                    "isPublicDomain": True,
                    "accessionNumber": "17.194.100",
                    "title": "Gold-Glass Roundel Fragment",
                    "objectName": "Roundel",
                    "medium": "Glass, gold leaf",
                    "dimensions": "Diam. 9.5 cm",
                    "measurements": [{"elementMeasurements": {"Height": 1.2, "Diameter": 9.5, "Weight": 0.38}}],
                    "objectDate": "4th century CE",
                    "objectBeginDate": 300,
                    "objectEndDate": 399,
                    "culture": "Roman",
                    "period": "Late Imperial",
                    "excavation": "Catacombs",
                    "city": "Rome",
                    "country": "Italy",
                    "department": "Medieval Art",
                    "repository": "The Metropolitan Museum of Art, New York",
                    "creditLine": "Gift of J. P. Morgan, 1917",
                    "objectURL": "https://www.metmuseum.org/art/collection/search/555001",
                    "primaryImage": "https://images.metmuseum.org/CRDImages/md/original/DP123.jpg",
                    "additionalImages": ["https://images.metmuseum.org/CRDImages/md/original/DP124.jpg"],
                    "tags": [{"term": "Craftworkers"}],
                })
            if "openaccess-api.clevelandart.org" in url:
                return _mock_response({
                    "data": [
                        # Duplicate by accession_number 2009.474 -> skipped
                        {
                            "id": 167883,
                            "accession_number": "2009.474",
                            "title": "Ribbed Glass Bowl",
                            "creation_date": "1–100 CE",
                            "creation_date_earliest": 1,
                            "creation_date_latest": 100,
                            "url": "https://clevelandart.org/art/2009.474",
                            "images": {"web": {"url": "https://openaccess-cdn.clevelandart.org/2009.474/web.jpg"}},
                        },
                        # New CMA record
                        {
                            "id": 199001,
                            "accession_number": "1985.12",
                            "title": "Blown Glass Unguentarium",
                            "type": "Vessel",
                            "technique": "Free-blown glass",
                            "culture": ["Roman, Syria"],
                            "find_spot": "Syria",
                            "creation_date": "2nd–3rd century CE",
                            "creation_date_earliest": 100,
                            "creation_date_latest": 299,
                            "measurements": "H. 12.0 cm",
                            "dimensions": {"overall": {"height": 0.12, "width": 0.045}},
                            "inscriptions": [{"inscription": "EUTYCHES"}],
                            "citations": [{"citation": "CMA Bulletin 1986, p. 14"}],
                            "description": "<p>Tall blown glass flask.</p>",
                            "collection": "GR - Roman",
                            "url": "https://clevelandart.org/art/1985.12",
                            "images": {"web": {"url": "https://openaccess-cdn.clevelandart.org/1985.12/web.jpg"}},
                            "alternate_images": [],
                        },
                    ]
                })
            if "api.vam.ac.uk/v2/objects/search" in url:
                return _mock_response({"records": [{"systemNumber": "O5328", "accessionNumber": "C.58-1963"}]})
            if "api.vam.ac.uk/v2/museumobject/O5328" in url:
                return _mock_response({
                    "record": {
                        "systemNumber": "O5328",
                        "accessionNumber": "C.58-1963",
                        "objectType": "Bowl",
                        "titles": [{"title": "Facet-cut Glass Cup"}],
                        "materialsAndTechniques": "Cut glass",
                        "summaryDescription": "<p>Sasanian wheel-cut glass vessel.</p>",
                        "dimensions": [{"dimension": "Height", "value": "8.2", "unit": "cm"}],
                        "productionDates": [{"date": {"text": "6th–7th century CE", "earliest": "0500-01-01", "latest": "0700-12-31"}, "association": {"text": "made"}}],
                        "placesOfOrigin": [{"place": {"text": "Iran"}, "association": {"text": "made"}}],
                        "marksAndInscriptions": [],
                        "bibliographicReferences": [{"free": "Erdmann 1961, p. 33"}],
                        "collectionCode": "ME",
                        "images": ["2006AF6997"],
                        "categories": [{"text": "Glass"}],
                    }
                })
            raise AssertionError(f"Unexpected GET URL: {url}")

        def fake_post(url, json=None, headers=None, timeout=10):
            assert "api.artic.edu/api/v1/artworks/search" in url
            return _mock_response({
                "config": {"iiif_url": "https://www.artic.edu/iiif/2"},
                "data": [{
                    "id": 61600,
                    "title": "Roman Glass Beaker",
                    "artwork_type_title": "Vessel",
                    "medium_display": "Mold-blown glass",
                    "dimensions": "10.5 × 8.0 cm",
                    "dimensions_detail": [{"height": 10.5, "width": 8.0, "depth": None}],
                    "date_display": "1st century CE",
                    "date_start": 1,
                    "date_end": 100,
                    "place_of_origin": "Rome",
                    "main_reference_number": "1981.11",
                    "description": "<p>Mold-blown <strong>Roman</strong> beaker.</p>",
                    "inscriptions": "<p>ENNIOS</p>",
                    "publication_history": "AIC Annual Report 1981.",
                    "image_id": "aee665f2-bb63-2a25-832e-260b73c278a8",
                    "alt_image_ids": [],
                    "term_titles": ["glassware", "Roman"],
                    "style_title": "Early Imperial",
                    "is_public_domain": True,
                }],
            })

        mock_get.side_effect = fake_get
        mock_post.side_effect = fake_post

        # Act
        res = client.post("/admin/discovery/search", json={
            "museums": ["met", "cma", "aic", "vam"],
            "keywords": ["glass"],
            "date_start": 0,
            "date_end": 899,
            "limit_per_museum": 5,
        })

        # Assert
        assert res.status_code == 200
        data = res.json()
        assert data["total_new"] == 4
        assert data["total_duplicates_skipped"] == 2  # 241792 + 2009.474

        by_museum = {c["museum_id"]: c for c in data["candidates"]}
        assert set(by_museum.keys()) == {"met", "cma", "aic", "vam"}

        # Met assertions
        met = by_museum["met"]
        assert met["completeness"] == "Fragmentary"
        assert met["weight"] == "0.38 kg"
        assert met["height"] == 1.2
        assert met["width"] == 9.5
        assert len(met["images"]) == 2
        assert met["latitude"] is not None

        # CMA meters -> cm conversion & inscriptions
        cma = by_museum["cma"]
        assert cma["height"] == 12.0
        assert cma["width"] == 4.5
        assert cma["inscription_present"] is True
        assert cma["inscription_1"] == "EUTYCHES"
        assert "CMA Bulletin 1986" in cma["publications"]

        # AIC HTML stripping & IIIF URL
        aic = by_museum["aic"]
        assert "<p>" not in aic["description"]
        assert "Mold-blown Roman beaker." in aic["description"]
        assert aic["inscription_1"] == "ENNIOS"
        assert aic["images"][0]["file_url"] == "https://www.artic.edu/iiif/2/aee665f2-bb63-2a25-832e-260b73c278a8/full/843,/0/default.jpg"

        # V&A Framemark IIIF URL & publications
        vam = by_museum["vam"]
        assert vam["height"] == 8.2
        assert vam["publications"] == "Erdmann 1961, p. 33"
        assert vam["images"][0]["file_url"] == "https://framemark.vam.ac.uk/collections/2006AF6997/full/!800,800/0/default.jpg"

    @patch("src.services.museum_discovery_service.requests.get")
    def test_search_withinBatchCrossKeywordDuplicate_isDeduplicated(self, mock_get, client):
        # Arrange: same CMA record returned for two different keywords
        _login_admin(client)
        mock_get.return_value = _mock_response({
            "data": [{
                "id": 200010,
                "accession_number": "1990.5",
                "title": "Roman Glass Jar",
                "creation_date": "200 CE",
                "creation_date_earliest": 200,
                "creation_date_latest": 200,
                "url": "https://clevelandart.org/art/1990.5",
                "images": {"web": {"url": "https://openaccess-cdn.clevelandart.org/1990.5/web.jpg"}},
            }]
        })

        # Act
        res = client.post("/admin/discovery/search", json={
            "museums": ["cma"],
            "keywords": ["glass", "roman"],
            "date_start": 0,
            "date_end": 899,
            "limit_per_museum": 10,
        })

        # Assert: appears once, second keyword hit skipped
        assert res.status_code == 200
        data = res.json()
        assert data["total_new"] == 1
        assert data["total_duplicates_skipped"] == 1


class TestDiscoveryEdgeAndExtraordinaryCases:
    """Edge, partial failure, validation, SSRF, and duplicate-safe import tests."""

    @patch("src.services.museum_discovery_service.requests.post")
    @patch("src.services.museum_discovery_service.requests.get")
    def test_search_partialMuseumTimeoutAndMet404_handlesGracefully(self, mock_get, mock_post, client):
        # Arrange: Met returns a 404 object ID; CMA times out; AIC succeeds
        _login_admin(client)

        def fake_get(url, params=None, headers=None, timeout=10):
            if "metmuseum.org/public/collection/v1.1/search" in url:
                return _mock_response({"objectIDs": [99999999]})
            if "metmuseum.org/public/collection/v1/objects/99999999" in url:
                return _mock_response({}, status_code=404)
            if "clevelandart.org" in url:
                raise requests.Timeout("CMA timed out")
            raise AssertionError(f"Unexpected URL: {url}")

        mock_get.side_effect = fake_get
        mock_post.return_value = _mock_response({
            "config": {"iiif_url": "https://www.artic.edu/iiif/2"},
            "data": [{
                "id": 777,
                "title": "Byzantine Lamp",
                "date_display": "500 CE",
                "date_start": 500,
                "date_end": 500,
                "main_reference_number": "1950.77",
                "image_id": "img-777",
                "is_public_domain": True,
            }],
        })

        # Act
        res = client.post("/admin/discovery/search", json={
            "museums": ["met", "cma", "aic"],
            "keywords": ["lamp"],
            "date_start": 0,
            "date_end": 899,
            "limit_per_museum": 5,
        })

        # Assert
        assert res.status_code == 200
        data = res.json()
        assert data["total_new"] == 1
        reports = {r["museum_id"]: r for r in data["museum_reports"]}
        assert reports["met"]["error"] is None
        assert "CMA timed out" in reports["cma"]["error"]
        assert reports["aic"]["new_count"] == 1

    def test_search_invalidInputs_return422(self, client):
        # Arrange
        _login_admin(client)

        # Act & Assert: inverted date range, empty keywords, invalid museum
        assert client.post("/admin/discovery/search", json={
            "museums": ["met"], "keywords": ["glass"], "date_start": 900, "date_end": 100
        }).status_code == 422
        assert client.post("/admin/discovery/search", json={
            "museums": ["met"], "keywords": ["   "], "date_start": 0, "date_end": 899
        }).status_code == 422
        assert client.post("/admin/discovery/search", json={
            "museums": ["louvre_invalid"], "keywords": ["glass"], "date_start": 0, "date_end": 899
        }).status_code == 422

    @patch("src.services.museum_discovery_service.download_and_store_image")
    def test_import_stagesPendingObjectsCachesImagesAndPreventsReimport(self, mock_store, client):
        # Arrange
        _login_admin(client)
        mock_store.return_value = "/api/images/cma_1985_12.jpg"

        candidate_payload = {
            "museum_id": "cma",
            "museum_name": "Cleveland Museum of Art",
            "source_record_id": "199001",
            "object_type": "Blown Glass Unguentarium",
            "material": "Free-blown glass",
            "findspot": "Syria",
            "production_location": "Roman, Syria",
            "present_location": "The Cleveland Museum of Art, Cleveland",
            "latitude": 34.8021,
            "longitude": 38.9968,
            "inventory_number": "1985.12",
            "description": "Tall blown glass flask.",
            "date_display": "2nd–3rd century CE",
            "date_start": 100,
            "date_end": 299,
            "height": 12.0,
            "width": 4.5,
            "unit": "cm",
            "inscription_present": True,
            "inscription_1": "EUTYCHES",
            "publications": "CMA Bulletin 1986",
            "external_url": "https://clevelandart.org/art/1985.12",
            "review_status": "accepted",  # Must be ignored; always staged as pending
            "tags": ["Roman", "Glass"],
            "images": [{
                "file_url": "https://openaccess-cdn.clevelandart.org/1985.12/web.jpg",
                "image_type": "Colour photo",
                "view_type": "Front",
                "image_sequence": 1,
                "source_identifier": "CMA 1985.12",
                "source_citation": "The Cleveland Museum of Art. 1985.12.",
            }],
        }

        # Act 1: First import succeeds with review_status="pending"
        res1 = client.post("/admin/discovery/import", json={"candidates": [candidate_payload]})
        assert res1.status_code == 200
        d1 = res1.json()
        assert d1["imported_count"] == 1
        assert d1["duplicates_skipped"] == 0
        assert d1["imported_objects"][0]["review_status"] == "pending"

        obj_id = d1["imported_objects"][0]["id"]
        detail = client.get(f"/objects/{obj_id}").json()
        assert detail["review_status"] == "pending"
        assert detail["images"][0]["file_url"] == "/api/images/cma_1985_12.jpg"
        assert detail["tags"] == ["Glass", "Roman"]

        # Act 2: Re-import of same candidate is skipped as duplicate
        res2 = client.post("/admin/discovery/import", json={"candidates": [candidate_payload]})
        assert res2.status_code == 200
        d2 = res2.json()
        assert d2["imported_count"] == 0
        assert d2["duplicates_skipped"] == 1
        assert d2["skipped_inventory_numbers"] == ["1985.12"]

    def test_import_ssrfDisallowedImageUrl_returns422(self, client):
        # Arrange
        _login_admin(client)

        # Act
        res = client.post("/admin/discovery/import", json={
            "candidates": [{
                "museum_id": "cma",
                "museum_name": "Cleveland Museum of Art",
                "source_record_id": "99",
                "object_type": "Bowl",
                "date_display": "100 CE",
                "date_start": 100,
                "date_end": 100,
                "images": [{
                    "file_url": "http://169.254.169.254/latest/meta-data/",
                    "image_sequence": 1,
                }],
            }]
        })

        # Assert
        assert res.status_code == 422


class TestPersistentDiscoveryKeywords:
    """Normal, Edge, and Extraordinary tests for persistent /admin/discovery/keywords."""

    def test_keywords_unauthenticated_return401(self, client):
        # Act & Assert
        assert client.get("/admin/discovery/keywords").status_code == 401
        assert client.post("/admin/discovery/keywords", json={"keyword": "gold-glass"}).status_code == 401
        assert client.delete("/admin/discovery/keywords", params={"keyword": "gold-glass"}).status_code == 401

    @patch("src.services.museum_discovery_service.requests.get")
    def test_keywords_addPersistsAcrossMuseumsListAndSearchAndDeleteRemoves(self, mock_get, client):
        # Arrange
        _login_admin(client)
        mock_get.return_value = _mock_response({"data": []})

        # Act 1 (Normal): Explicitly add a keyword
        add_res = client.post("/admin/discovery/keywords", json={"keyword": "  gold-glass  "})
        assert add_res.status_code == 200
        add_data = add_res.json()
        assert add_data["keyword"] == "gold-glass"
        assert add_data["created"] is True
        assert "gold-glass" in add_data["keywords"]

        # Assert 1: Saved keyword appears in both /keywords and /museums default_keywords
        assert "gold-glass" in client.get("/admin/discovery/keywords").json()
        museums = client.get("/admin/discovery/museums").json()
        assert all("gold-glass" in m["default_keywords"] for m in museums)

        # Act 2 (Edge): Re-adding case-insensitively does not duplicate
        dup_res = client.post("/admin/discovery/keywords", json={"keyword": "  GOLD-GLASS  "})
        assert dup_res.status_code == 200
        assert dup_res.json()["created"] is False
        assert sum(1 for k in dup_res.json()["keywords"] if k.lower() == "gold-glass") == 1

        # Act 3 (Normal): Implicit persistence when running a search with a new keyword
        search_res = client.post("/admin/discovery/search", json={
            "museums": ["cma"],
            "keywords": ["mosaic", "gold-glass"],
            "date_start": 0,
            "date_end": 899,
            "limit_per_museum": 5,
        })
        assert search_res.status_code == 200
        assert "mosaic" in client.get("/admin/discovery/keywords").json()

        # Act 4 (Normal): Removing a keyword persists removal (HTTP 204)
        del_res = client.delete("/admin/discovery/keywords", params={"keyword": "gold-glass"})
        assert del_res.status_code == 204
        assert "gold-glass" not in client.get("/admin/discovery/keywords").json()
        assert "mosaic" in client.get("/admin/discovery/keywords").json()

    def test_keywords_extraordinaryBlankAndTooLongAndMaxCap_rejected(self, client, monkeypatch):
        # Arrange
        _login_admin(client)
        from src.services import museum_discovery_service

        # Act & Assert: blank, control chars, >80 chars -> 422
        assert client.post("/admin/discovery/keywords", json={"keyword": "   "}).status_code == 422
        assert client.post("/admin/discovery/keywords", json={"keyword": "bad\x00kw"}).status_code == 422
        assert client.post("/admin/discovery/keywords", json={"keyword": "x" * 81}).status_code == 422

        # Act & Assert: exceeding MAX_SAVED_KEYWORDS -> 400 ValidationError
        monkeypatch.setattr(museum_discovery_service, "MAX_SAVED_KEYWORDS", 8)
        cap_res = client.post("/admin/discovery/keywords", json={"keyword": "mosaic"})
        assert cap_res.status_code == 400
        assert "Maximum of 8" in cap_res.json()["detail"]
