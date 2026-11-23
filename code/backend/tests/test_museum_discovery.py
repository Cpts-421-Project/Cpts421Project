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

import json
import threading
from unittest.mock import MagicMock, patch
import pytest
import requests
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.main import app, _rate_limit_store
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
    _rate_limit_store.clear()
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
        existing_bm = Object(
            object_type="Gold-Glass Medallion",
            present_location="The British Museum, London",
            date_display="4th century CE",
            date_start=301,
            date_end=400,
            inventory_number="1958,1202.1",
            external_url="https://www.britishmuseum.org/collection/object/G_1958-1202-1",
            review_status="accepted",
        )
        db.add_all([existing_met, existing_cma, existing_bm])

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

    def test_listMuseums_authenticatedAdmin_returnsFivePredefinedMuseums(self, client):
        # Arrange
        _login_admin(client)

        # Act
        res = client.get("/admin/discovery/museums")

        # Assert
        assert res.status_code == 200
        museums = res.json()
        assert [m["id"] for m in museums] == ["met", "cma", "aic", "vam", "bm"]
        bm_entry = next(m for m in museums if m["id"] == "bm")
        assert bm_entry["name"] == "The British Museum"
        assert bm_entry["present_location"] == "The British Museum, London"
        for m in museums:
            assert m["default_date_start"] == 0
            assert m["default_date_end"] == 899
            assert len(m["default_keywords"]) >= 1


class TestMuseumAdaptersAndFullFields:
    """Verify full 2_excel field mapping & deduplication across all 5 museum adapters."""

    @patch("src.services.museum_discovery_service.requests.post")
    @patch("src.services.museum_discovery_service.requests.get")
    def test_search_allFiveMuseums_extractsFullMetadataAndSkipsDuplicates(self, mock_get, mock_post, client):
        # Arrange
        _login_admin(client)

        def fake_get(url, params=None, headers=None, timeout=10):
            params = params or {}
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
            if "www.wikidata.org/w/api.php" in url:
                if params.get("list") == "search":
                    assert "haswbstatement:P195=Q6373|P276=Q6373" in params.get("srsearch", "")
                    return _mock_response({
                        "query": {
                            "search": [
                                {"title": "Q900001"},  # Duplicate inv 1958,1202.1
                                {"title": "Q2457011"},  # New BM artifact
                            ]
                        }
                    })
                if params.get("action") == "wbgetentities" and "claims" in params.get("props", ""):
                    return _mock_response({
                        "entities": {
                            "Q900001": {
                                "id": "Q900001",
                                "labels": {"en": {"value": "Gold-Glass Medallion"}},
                                "claims": {
                                    "P31": [{"rank": "normal", "mainsnak": {"snaktype": "value", "datavalue": {"type": "wikibase-entityid", "value": {"id": "Q3305213"}}}}],
                                    "P217": [{"rank": "normal", "mainsnak": {"snaktype": "value", "datavalue": {"type": "string", "value": "1958,1202.1"}}}],
                                    "P571": [{"rank": "normal", "mainsnak": {"snaktype": "value", "datavalue": {"type": "time", "value": {"time": "+0400-01-01T00:00:00Z", "precision": 7}}}}],
                                    "P18": [{"rank": "normal", "mainsnak": {"snaktype": "value", "datavalue": {"type": "string", "value": "Gold_glass_bm.jpg"}}}],
                                },
                            },
                            "Q2457011": {
                                "id": "Q2457011",
                                "labels": {"en": {"value": "Vindolanda Copper-Alloy Stylus"}},
                                "descriptions": {"en": {"value": "Roman writing stylus found at Vindolanda"}},
                                "claims": {
                                    "P31": [{"rank": "normal", "mainsnak": {"snaktype": "value", "datavalue": {"type": "wikibase-entityid", "value": {"id": "Q220659"}}}}],
                                    "P186": [{"rank": "normal", "mainsnak": {"snaktype": "value", "datavalue": {"type": "wikibase-entityid", "value": {"id": "Q39782"}}}}],
                                    "P189": [{"rank": "normal", "mainsnak": {"snaktype": "value", "datavalue": {"type": "wikibase-entityid", "value": {"id": "Q1775225"}}}}],
                                    "P1071": [{"rank": "normal", "mainsnak": {"snaktype": "value", "datavalue": {"type": "wikibase-entityid", "value": {"id": "Q1747689"}}}}],
                                    "P2596": [{"rank": "normal", "mainsnak": {"snaktype": "value", "datavalue": {"type": "wikibase-entityid", "value": {"id": "Q1747689"}}}}],
                                    "P2348": [{"rank": "normal", "mainsnak": {"snaktype": "value", "datavalue": {"type": "wikibase-entityid", "value": {"id": "Q1747689"}}}}],
                                    "P571": [{"rank": "normal", "mainsnak": {"snaktype": "value", "datavalue": {"type": "time", "value": {"time": "+0200-01-01T00:00:00Z", "precision": 7}}}}],
                                    "P217": [{
                                        "rank": "normal",
                                        "mainsnak": {"snaktype": "value", "datavalue": {"type": "string", "value": "1986,1001.15"}},
                                        "qualifiers": {"P195": [{"snaktype": "value", "datavalue": {"type": "wikibase-entityid", "value": {"id": "Q6373"}}}]},
                                    }],
                                    "P2048": [{"rank": "normal", "mainsnak": {"snaktype": "value", "datavalue": {"type": "quantity", "value": {"amount": "+125", "unit": "http://www.wikidata.org/entity/Q174789"}}}}],
                                    "P2049": [{"rank": "normal", "mainsnak": {"snaktype": "value", "datavalue": {"type": "quantity", "value": {"amount": "+0.8", "unit": "http://www.wikidata.org/entity/Q174728"}}}}],
                                    "P2067": [{"rank": "normal", "mainsnak": {"snaktype": "value", "datavalue": {"type": "quantity", "value": {"amount": "+18.5", "unit": "http://www.wikidata.org/entity/Q41803"}}}}],
                                    "P1684": [{"rank": "normal", "mainsnak": {"snaktype": "value", "datavalue": {"type": "monolingualtext", "value": {"text": "ME FECIT", "language": "la"}}}}],
                                    "P1343": [{"rank": "normal", "mainsnak": {"snaktype": "value", "datavalue": {"type": "wikibase-entityid", "value": {"id": "Q110001"}}}}],
                                    "P625": [{"rank": "normal", "mainsnak": {"snaktype": "value", "datavalue": {"type": "globecoordinate", "value": {"latitude": 54.9912, "longitude": -2.3607}}}}],
                                    "P973": [{"rank": "normal", "mainsnak": {"snaktype": "value", "datavalue": {"type": "string", "value": "https://www.britishmuseum.org/collection/object/H_1986-1001-15"}}}],
                                    "P18": [{"rank": "normal", "mainsnak": {"snaktype": "value", "datavalue": {"type": "string", "value": "Vindolanda_stylus_BM.jpg"}}}],
                                },
                            },
                        }
                    })
                if params.get("action") == "wbgetentities":
                    return _mock_response({
                        "entities": {
                            "Q220659": {"id": "Q220659", "labels": {"en": {"value": "archaeological artifact"}}},
                            "Q39782": {"id": "Q39782", "labels": {"en": {"value": "bronze"}}},
                            "Q1775225": {"id": "Q1775225", "labels": {"en": {"value": "Vindolanda"}}},
                            "Q1747689": {"id": "Q1747689", "labels": {"en": {"value": "Ancient Rome"}}},
                            "Q110001": {"id": "Q110001", "labels": {"en": {"value": "Britannia Roman Catalogue 1990"}}},
                            "Q3305213": {"id": "Q3305213", "labels": {"en": {"value": "medallion"}}},
                        }
                    })
            if "commons.wikimedia.org/w/api.php" in url:
                return _mock_response({
                    "query": {
                        "normalized": [
                            {"from": "File:Vindolanda_stylus_BM.jpg", "to": "File:Vindolanda stylus BM.jpg"},
                        ],
                        "pages": {
                            "101": {
                                "title": "File:Vindolanda stylus BM.jpg",
                                "imageinfo": [{
                                    "url": "https://upload.wikimedia.org/wikipedia/commons/a/ab/Vindolanda_stylus_BM.jpg",
                                    "thumburl": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Vindolanda_stylus_BM.jpg/1000px-Vindolanda_stylus_BM.jpg",
                                    "extmetadata": {
                                        "ImageDescription": {"value": "<p>Iron and bronze writing stylus from Vindolanda.</p>"},
                                    },
                                }],
                            }
                        },
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
            "museums": ["met", "cma", "aic", "vam", "bm"],
            "keywords": ["glass"],
            "date_start": 0,
            "date_end": 899,
            "limit_per_museum": 5,
        })

        # Assert
        assert res.status_code == 200
        data = res.json()
        assert data["total_new"] == 5
        assert data["total_duplicates_skipped"] == 3  # 241792 + 2009.474 + 1958,1202.1

        by_museum = {c["museum_id"]: c for c in data["candidates"]}
        assert set(by_museum.keys()) == {"met", "cma", "aic", "vam", "bm"}

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

        # British Museum (Wikidata + Wikimedia Commons) assertions
        bm = by_museum["bm"]
        assert bm["inventory_number"] == "1986,1001.15"
        assert bm["present_location"] == "The British Museum, London"
        assert bm["date_display"] == "2nd century CE"
        assert bm["date_start"] == 101
        assert bm["date_end"] == 200
        assert bm["material"] == "bronze"
        assert bm["findspot"] == "Vindolanda"
        assert bm["height"] == 12.5
        assert bm["width"] == 0.8
        assert bm["weight"] == "18.5 g"
        assert bm["inscription_present"] is True
        assert bm["inscription_1"] == "ME FECIT"
        assert bm["publications"] == "Britannia Roman Catalogue 1990"
        assert bm["latitude"] == 54.9912
        assert bm["longitude"] == -2.3607
        assert bm["external_url"] == "https://www.britishmuseum.org/collection/object/H_1986-1001-15"
        assert bm["images"][0]["file_url"] == "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Vindolanda_stylus_BM.jpg/1000px-Vindolanda_stylus_BM.jpg"
        assert bm["images"][0]["source_identifier"] == "BM Q2457011 / File:Vindolanda_stylus_BM.jpg"
        assert "Iron and bronze writing stylus from Vindolanda." in bm["description"]

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
        cap = len(museum_discovery_service.DEFAULT_KEYWORDS)
        monkeypatch.setattr(museum_discovery_service, "MAX_SAVED_KEYWORDS", cap)
        cap_res = client.post("/admin/discovery/keywords", json={"keyword": "mosaic"})
        assert cap_res.status_code == 400
        assert f"Maximum of {cap}" in cap_res.json()["detail"]

    @patch("src.services.museum_discovery_service.requests.get")
    def test_keywords_defaultsIncludeAllDatacollectionKeywordsFileTerms(self, mock_get, client):
        # Arrange: authenticate admin and read raw datacollection/keywords file
        _login_admin(client)
        from pathlib import Path
        from src.services import museum_discovery_service

        keywords_file = Path(__file__).resolve().parents[1] / "datacollection" / "keywords"
        raw_lines = keywords_file.read_text(encoding="utf-8").splitlines()
        file_terms = [line.lstrip(",").strip() for line in raw_lines if line.lstrip(",").strip()]
        assert len(file_terms) == 60

        # Act
        saved = client.get("/admin/discovery/keywords").json()
        museums = client.get("/admin/discovery/museums").json()

        # Assert: all 60 file terms + 2 curated extra defaults = 62 unique terms without leading commas
        assert len(saved) == 62
        assert len({k.lower() for k in saved}) == 62
        assert all(not k.startswith(",") for k in saved)
        saved_lower = {k.lower() for k in saved}
        for term in file_terms:
            assert term.lower() in saved_lower
        assert "glass" in saved_lower
        assert "workshop" in saved_lower
        assert len(museum_discovery_service.DEFAULT_KEYWORDS) == 62
        assert all(m["default_keywords"] == saved for m in museums)

        # Assert search endpoint accepts all 62 keywords at once without 422
        mock_get.return_value = _mock_response({"data": []})
        search_res = client.post("/admin/discovery/search", json={
            "museums": ["cma"],
            "keywords": saved,
            "date_start": 0,
            "date_end": 899,
            "limit_per_museum": 5,
        })
        assert search_res.status_code == 200


class TestDiscoveryProgressStreaming:
    """Normal, Edge, and Extraordinary tests for NDJSON progress streaming (/admin/discovery/search/stream)."""

    @patch("src.services.museum_discovery_service.requests.post")
    @patch("src.services.museum_discovery_service.requests.get")
    def test_streamSearch_allMuseums_emitsOrderedProgressEventsAndFinalResult(self, mock_get, mock_post, client):
        # Arrange
        _login_admin(client)

        def fake_get(url, params=None, headers=None, timeout=10):
            if "metmuseum.org/public/collection/v1.1/search" in url:
                return _mock_response({"total": 1, "objectIDs": [555001]})
            if url.endswith("/objects/555001"):
                return _mock_response({
                    "objectID": 555001,
                    "isPublicDomain": True,
                    "accessionNumber": "17.194.100",
                    "title": "Gold-Glass Roundel Fragment",
                    "medium": "Glass, gold leaf",
                    "objectDate": "4th century CE",
                    "objectBeginDate": 300,
                    "objectEndDate": 399,
                    "city": "Rome",
                    "country": "Italy",
                    "objectURL": "https://www.metmuseum.org/art/collection/search/555001",
                    "primaryImage": "https://images.metmuseum.org/CRDImages/md/original/DP123.jpg",
                })
            raise AssertionError(f"Unexpected GET URL: {url}")

        mock_get.side_effect = fake_get
        mock_post.return_value = _mock_response({
            "config": {"iiif_url": "https://www.artic.edu/iiif/2"},
            "data": [{
                "id": 61600,
                "title": "Roman Glass Beaker",
                "medium_display": "Mold-blown glass",
                "date_display": "1st century CE",
                "date_start": 1,
                "date_end": 100,
                "place_of_origin": "Rome",
                "main_reference_number": "1981.11",
                "image_id": "aee665f2-bb63-2a25-832e-260b73c278a8",
                "is_public_domain": True,
            }],
        })

        # Act
        with client.stream("POST", "/admin/discovery/search/stream", json={
            "museums": ["met", "aic"],
            "keywords": ["glass"],
            "date_start": 0,
            "date_end": 899,
            "limit_per_museum": 5,
        }) as res:
            assert res.status_code == 200
            assert "application/x-ndjson" in res.headers["content-type"]
            assert res.headers.get("x-accel-buffering") == "no"
            assert res.headers.get("cache-control") == "no-cache"
            events = [json.loads(line) for line in res.iter_lines() if line]

        # Assert ordered event lifecycle and final payload
        event_types = [e["type"] for e in events]
        assert event_types[0] == "search_started"
        assert event_types[-1] == "complete"
        assert events[0]["total_museums"] == 2
        assert events[0]["total_keywords"] == 1
        assert "museum_started" in event_types
        assert "keyword_searching" in event_types
        assert "detail_fetching" in event_types
        assert event_types.count("candidate_found") == 2
        assert event_types.count("museum_completed") == 2

        detail_evt = next(e for e in events if e["type"] == "detail_fetching")
        assert detail_evt["museum_id"] == "met"
        assert detail_evt["detail_index"] == 1
        assert detail_evt["detail_total"] == 1

        complete_evt = events[-1]
        assert complete_evt["total_new"] == 2
        assert len(complete_evt["result"]["candidates"]) == 2
        assert len(complete_evt["result"]["museum_reports"]) == 2

    @patch("src.services.museum_discovery_service.requests.post")
    @patch("src.services.museum_discovery_service.requests.get")
    def test_streamSearch_partialMuseumTimeoutAndCancellation_handledCleanly(self, mock_get, mock_post, client):
        # Arrange: CMA times out while AIC succeeds
        _login_admin(client)
        mock_get.side_effect = requests.Timeout("CMA timed out")
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

        # Act 1 (Edge): Stream still completes cleanly when one museum fails
        with client.stream("POST", "/admin/discovery/search/stream", json={
            "museums": ["cma", "aic"],
            "keywords": ["lamp"],
            "date_start": 0,
            "date_end": 899,
            "limit_per_museum": 5,
        }) as res:
            assert res.status_code == 200
            events = [json.loads(line) for line in res.iter_lines() if line]

        completed_by_museum = {
            e["museum_id"]: e for e in events if e["type"] == "museum_completed"
        }
        assert "CMA timed out" in completed_by_museum["cma"]["error"]
        assert completed_by_museum["aic"]["error"] is None
        assert completed_by_museum["aic"]["new_count"] == 1
        assert events[-1]["type"] == "complete"
        assert events[-1]["total_new"] == 1

        # Act 2 (Edge): Pre-cancelled worker stops before making outbound HTTP calls
        mock_get.reset_mock()
        mock_post.reset_mock()
        db = TestingSessionLocal()
        try:
            from src.services.museum_discovery_service import MuseumDiscoveryService
            from src.schemas import DiscoverySearchRequest

            service = MuseumDiscoveryService(db)
            req = DiscoverySearchRequest(
                museums=["cma"],
                keywords=["lamp"],
                date_start=0,
                date_end=899,
                limit_per_museum=5,
            )
            index = service.prepare_discovery(req)
            cancel_event = threading.Event()
            cancel_event.set()
            recorded = []
            MuseumDiscoveryService.discover_with_index(
                req,
                index,
                progress_callback=recorded.append,
                cancel_event=cancel_event,
            )
        finally:
            db.close()

        mock_get.assert_not_called()
        assert [e["type"] for e in recorded] == ["search_started"]

    def test_streamSearch_unauthenticatedAndInvalidPayloads_rejectedBeforeStreaming(self, client):
        # Act & Assert: 401 when unauthenticated
        assert client.post("/admin/discovery/search/stream", json={
            "museums": ["met"], "keywords": ["glass"], "date_start": 0, "date_end": 899
        }).status_code == 401

        # Authenticate then verify 422 validation errors
        _login_admin(client)
        assert client.post("/admin/discovery/search/stream", json={
            "museums": ["met"], "keywords": ["glass"], "date_start": 900, "date_end": 100
        }).status_code == 422
        assert client.post("/admin/discovery/search/stream", json={
            "museums": ["louvre_invalid"], "keywords": ["glass"], "date_start": 0, "date_end": 899
        }).status_code == 422

    def test_streamSearch_unexpectedWorkerException_emitsTerminalErrorEvent(self, client):
        # Arrange
        _login_admin(client)

        with patch(
            "src.services.museum_discovery_service.MuseumDiscoveryService.discover_with_index",
            side_effect=RuntimeError("boom"),
        ):
            # Act
            with client.stream("POST", "/admin/discovery/search/stream", json={
                "museums": ["met"],
                "keywords": ["glass"],
                "date_start": 0,
                "date_end": 899,
                "limit_per_museum": 5,
            }) as res:
                assert res.status_code == 200
                events = [json.loads(line) for line in res.iter_lines() if line]

        # Assert
        assert len(events) == 1
        assert events[0]["type"] == "error"
        assert "boom" in events[0]["message"]


class TestReviewQueueImageFallbackAndRecovery:
    """Tests for discovery import fallback URL preservation and pending queue image recovery."""

    @patch("src.services.museum_discovery_service.download_and_store_image", return_value=None)
    def test_import_whenBucketCachingFails_preservesValidatedUrlsInPendingQueue(self, _mock_store, client):
        # Arrange
        _login_admin(client)
        cma_img = "https://openaccess-cdn.clevelandart.org/1985.12/web.jpg"
        met_img = "https://images.metmuseum.org/CRDImages/md/original/DP123.jpg"

        candidates = [
            {
                "museum_id": "cma",
                "museum_name": "Cleveland Museum of Art",
                "source_record_id": "199001",
                "object_type": "Blown Glass Unguentarium",
                "present_location": "The Cleveland Museum of Art, Cleveland",
                "inventory_number": "1985.12",
                "date_display": "2nd–3rd century CE",
                "date_start": 100,
                "date_end": 299,
                "external_url": "https://clevelandart.org/art/1985.12",
                "images": [{"file_url": cma_img, "image_sequence": 1, "source_identifier": "CMA 1985.12"}],
            },
            {
                "museum_id": "met",
                "museum_name": "The Metropolitan Museum of Art",
                "source_record_id": "555001",
                "object_type": "Gold-Glass Fragment",
                "present_location": "The Metropolitan Museum of Art, New York",
                "inventory_number": "17.194.100",
                "date_display": "4th century CE",
                "date_start": 300,
                "date_end": 399,
                "external_url": "https://www.metmuseum.org/art/collection/search/555001",
                "images": [{"file_url": met_img, "image_sequence": 1, "source_identifier": "Met Object ID 555001"}],
            },
        ]

        # Act
        imp_res = client.post("/admin/discovery/import", json={"candidates": candidates})
        assert imp_res.status_code == 200
        assert imp_res.json()["imported_count"] == 2

        pending_res = client.get("/objects/pending")
        assert pending_res.status_code == 200
        by_inv = {item["inventory_number"]: item for item in pending_res.json()}

        # Assert: neither URL was wiped to "" nor mangled to a non-existent /api/images/met_*.jpg
        assert by_inv["1985.12"]["images"][0]["file_url"] == cma_img
        assert by_inv["17.194.100"]["images"][0]["file_url"] == met_img

    @patch("src.services.museum_discovery_service.requests.get")
    @patch("src.services.museum_discovery_service.download_and_store_image")
    def test_recoverObjectImages_normalPendingVamAndMet_recoversAndCachesOrFallsBack(self, mock_store, mock_get, client):
        # Arrange: seed pending V&A (empty file_url) and pending Met (empty file_url)
        _login_admin(client)
        db = TestingSessionLocal()
        try:
            vam_obj = Object(
                object_type="Facet-cut Glass Cup",
                present_location="Victoria and Albert Museum, London",
                date_display="6th century CE",
                date_start=500,
                date_end=599,
                inventory_number="C.58-1963",
                external_url="https://collections.vam.ac.uk/item/O5328",
                review_status="pending",
            )
            met_obj = Object(
                object_type="Gold-Glass Roundel",
                present_location="The Metropolitan Museum of Art, New York",
                date_display="4th century CE",
                date_start=300,
                date_end=399,
                inventory_number="17.194.100",
                external_url="https://www.metmuseum.org/art/collection/search/555001",
                review_status="pending",
            )
            db.add_all([vam_obj, met_obj])
            db.flush()
            db.add_all([
                Image(
                    object_id=vam_obj.id,
                    image_type="Colour photo",
                    view_type="Front",
                    image_sequence=1,
                    source_identifier="V&A O5328 / 2006AF6997",
                    file_url="",
                ),
                Image(
                    object_id=met_obj.id,
                    image_type="Colour photo",
                    view_type="Front",
                    image_sequence=1,
                    source_identifier="Met Object ID 555001",
                    file_url="",
                ),
            ])
            db.commit()
            vam_id = vam_obj.id
            met_id = met_obj.id
        finally:
            db.close()

        # Act 1: V&A recovers directly from source_identifier; if bucket fails, keeps Framemark HTTPS URL
        mock_store.return_value = None
        vam_res = client.post(f"/objects/{vam_id}/recover-images")
        assert vam_res.status_code == 200
        assert (
            vam_res.json()["images"][0]["file_url"]
            == "https://framemark.vam.ac.uk/collections/2006AF6997/full/!800,800/0/default.jpg"
        )

        # Act 2: Met queries collectionapi and caches to /api/images/... when bucket succeeds
        mock_get.return_value = _mock_response({
            "objectID": 555001,
            "primaryImage": "https://images.metmuseum.org/CRDImages/md/original/DP123.jpg",
        })
        mock_store.return_value = "/api/images/met_17_194_100_abc.jpg"

        met_res = client.post(f"/objects/{met_id}/recover-images")
        assert met_res.status_code == 200
        assert met_res.json()["images"][0]["file_url"] == "/api/images/met_17_194_100_abc.jpg"

    @patch("src.services.museum_discovery_service.requests.get")
    def test_recoverObjectImages_edgeAlreadyHasValidUrl_isIdempotentNoOp(self, mock_get, client):
        # Arrange
        _login_admin(client)
        db = TestingSessionLocal()
        try:
            obj = Object(
                object_type="Already Imaged Lamp",
                date_display="200 CE",
                date_start=200,
                date_end=200,
                inventory_number="OK-1",
                external_url="https://www.metmuseum.org/art/collection/search/555001",
                review_status="pending",
            )
            db.add(obj)
            db.flush()
            db.add(Image(object_id=obj.id, image_sequence=1, file_url="/api/images/existing.jpg"))
            db.commit()
            obj_id = obj.id
        finally:
            db.close()

        # Act
        res = client.post(f"/objects/{obj_id}/recover-images")

        # Assert
        assert res.status_code == 200
        assert res.json()["images"][0]["file_url"] == "/api/images/existing.jpg"
        mock_get.assert_not_called()

    @patch("src.services.museum_discovery_service.requests.get")
    def test_recoverObjectImages_extraordinaryAuthNotFoundAndUpstreamTimeout(self, mock_get, client):
        # Act 1: unauthenticated -> 401
        assert client.post("/objects/1/recover-images").status_code == 401

        # Act 2: authenticated missing object -> 404
        _login_admin(client)
        assert client.post("/objects/999999/recover-images").status_code == 404

        # Act 3: upstream museum timeout degrades gracefully without HTTP 500
        db = TestingSessionLocal()
        try:
            obj = Object(
                object_type="Timeout Test Object",
                date_display="300 CE",
                date_start=300,
                date_end=300,
                inventory_number="TO-1",
                external_url="https://www.metmuseum.org/art/collection/search/555999",
                review_status="pending",
            )
            db.add(obj)
            db.flush()
            db.add(Image(object_id=obj.id, image_sequence=1, source_identifier="Met Object ID 555999", file_url=""))
            db.commit()
            obj_id = obj.id
        finally:
            db.close()

        mock_get.side_effect = requests.Timeout("Met API timeout")
        res = client.post(f"/objects/{obj_id}/recover-images")
        assert res.status_code == 200
        assert res.json()["images"][0]["file_url"] == ""


class TestRejectedPiecesSkippedInFutureSearches:
    """Normal, Edge, and Extraordinary tests verifying rejected artifacts stay skipped."""

    @patch("src.services.museum_discovery_service.download_and_store_image", return_value="/api/images/met_17_194_100.jpg")
    @patch("src.services.museum_discovery_service.requests.get")
    def test_reviewQueueRejection_skipsFutureDiscoverySearchStreamAndImportWithoutDetailFetch(
        self, mock_get, _mock_store, client
    ):
        # Arrange: import a Met candidate (555001) and reject it via Review Queue
        _login_admin(client)
        candidate = {
            "museum_id": "met",
            "museum_name": "The Metropolitan Museum of Art",
            "source_record_id": "555001",
            "object_type": "Gold-Glass Roundel Fragment",
            "present_location": "The Metropolitan Museum of Art, New York",
            "inventory_number": "17.194.100",
            "date_display": "4th century CE",
            "date_start": 300,
            "date_end": 399,
            "external_url": "https://www.metmuseum.org/art/collection/search/555001",
            "images": [{
                "file_url": "https://images.metmuseum.org/CRDImages/md/original/DP123.jpg",
                "image_sequence": 1,
                "source_identifier": "Met Object ID 555001",
            }],
        }
        imp_res = client.post("/admin/discovery/import", json={"candidates": [candidate]})
        assert imp_res.status_code == 200
        obj_id = imp_res.json()["imported_objects"][0]["id"]

        rev_res = client.patch(f"/objects/{obj_id}/review", json={"status": "rejected"})
        assert rev_res.status_code == 200
        assert rev_res.json()["review_status"] == "rejected"

        detail_urls_called = []

        def fake_get(url, params=None, headers=None, timeout=10):
            if "metmuseum.org/public/collection/v1.1/search" in url:
                return _mock_response({"total": 1, "objectIDs": [555001]})
            detail_urls_called.append(url)
            raise AssertionError(f"Detail endpoint should not be fetched for skipped Met ID: {url}")

        mock_get.side_effect = fake_get

        # Act 1: Standard discovery search skips 555001 before any detail GET
        search_res = client.post("/admin/discovery/search", json={
            "museums": ["met"],
            "keywords": ["glass"],
            "date_start": 0,
            "date_end": 899,
            "limit_per_museum": 5,
        })
        assert search_res.status_code == 200
        data = search_res.json()
        assert data["total_new"] == 0
        assert data["total_duplicates_skipped"] == 1
        assert data["total_rejected_skipped"] == 1
        assert data["museum_reports"][0]["rejected_skipped"] == 1
        assert detail_urls_called == []

        # Act 2: Streaming search emits rejected_skipped counts cleanly
        with client.stream("POST", "/admin/discovery/search/stream", json={
            "museums": ["met"],
            "keywords": ["glass"],
            "date_start": 0,
            "date_end": 899,
            "limit_per_museum": 5,
        }) as stream_res:
            assert stream_res.status_code == 200
            events = [json.loads(line) for line in stream_res.iter_lines() if line]

        complete_evt = events[-1]
        assert complete_evt["type"] == "complete"
        assert complete_evt["total_rejected_skipped"] == 1
        assert complete_evt["result"]["total_rejected_skipped"] == 1

        # Act 3: Stale import of the rejected candidate is also skipped
        reimport_res = client.post("/admin/discovery/import", json={"candidates": [candidate]})
        assert reimport_res.status_code == 200
        assert reimport_res.json()["imported_count"] == 0
        assert reimport_res.json()["duplicates_skipped"] == 1

    @patch("src.services.museum_discovery_service.requests.post")
    @patch("src.services.museum_discovery_service.requests.get")
    def test_pruningOverThreeRejected_retainsJustRejectedLowerIdAndSkipsAllFiveForever(
        self, mock_get, mock_post, client
    ):
        # Arrange: seed 5 pending objects in ascending ID order across museums
        from src.models import RejectedArtifact

        _login_admin(client)
        db = TestingSessionLocal()
        try:
            objs = [
                Object(
                    object_type="Met Item 1 (Lowest ID)",
                    present_location="The Metropolitan Museum of Art, New York",
                    date_display="200 CE",
                    date_start=200,
                    date_end=200,
                    inventory_number="MET-LOW-1",
                    external_url="https://www.metmuseum.org/art/collection/search/700001",
                    review_status="pending",
                ),
                Object(
                    object_type="Met Item 2",
                    present_location="The Metropolitan Museum of Art, New York",
                    date_display="250 CE",
                    date_start=250,
                    date_end=250,
                    inventory_number="MET-2",
                    external_url="https://www.metmuseum.org/art/collection/search/700002",
                    review_status="pending",
                ),
                Object(
                    object_type="CMA Item 3",
                    present_location="The Cleveland Museum of Art, Cleveland",
                    date_display="300 CE",
                    date_start=300,
                    date_end=300,
                    inventory_number="CMA-700003",
                    external_url="https://clevelandart.org/art/CMA-700003",
                    review_status="pending",
                ),
                Object(
                    object_type="AIC Item 4",
                    present_location="The Art Institute of Chicago, Chicago",
                    date_display="350 CE",
                    date_start=350,
                    date_end=350,
                    inventory_number="1990.4",
                    external_url="https://www.artic.edu/artworks/700004",
                    review_status="pending",
                ),
                Object(
                    object_type="VAM Item 5",
                    present_location="Victoria and Albert Museum, London",
                    date_display="400 CE",
                    date_start=400,
                    date_end=400,
                    inventory_number="VAM-5",
                    external_url="https://collections.vam.ac.uk/item/O700005",
                    review_status="pending",
                ),
            ]
            db.add_all(objs)
            db.commit()
            ids = [o.id for o in objs]
        finally:
            db.close()

        # Act 1: Reject items 2..5 first, then reject item 1 (lowest ID) LAST
        for oid in [ids[1], ids[2], ids[3], ids[4], ids[0]]:
            res = client.patch(f"/objects/{oid}/review", json={"status": "rejected"})
            assert res.status_code == 200
            assert res.json()["review_status"] == "rejected"

        # Assert: 3 rejected Object rows kept (including lowest ID just rejected!), 5 tombstones saved
        db = TestingSessionLocal()
        try:
            kept_ids = {o.id for o in db.query(Object).filter(Object.review_status == "rejected").all()}
            assert len(kept_ids) == 3
            assert ids[0] in kept_ids  # Just-rejected lower-ID item was NOT immediately deleted
            assert db.query(RejectedArtifact).count() == 5
        finally:
            db.close()

        # Act 2: Future discovery across all 4 museums skips all 5 even after 2 were pruned
        def fake_get(url, params=None, headers=None, timeout=10):
            if "metmuseum.org/public/collection/v1.1/search" in url:
                return _mock_response({"objectIDs": [700001, 700002]})
            if "openaccess-api.clevelandart.org" in url:
                return _mock_response({
                    "data": [{
                        "id": 700003,
                        "accession_number": None,
                        "title": "CMA Item 3",
                        "creation_date": "300 CE",
                        "creation_date_earliest": 300,
                        "creation_date_latest": 300,
                        "url": "https://clevelandart.org/art/CMA-700003",
                        "images": {"web": {"url": "https://openaccess-cdn.clevelandart.org/700003/web.jpg"}},
                    }]
                })
            if "api.vam.ac.uk/v2/objects/search" in url:
                return _mock_response({"records": [{"systemNumber": "O700005", "accessionNumber": "VAM-5"}]})
            raise AssertionError(f"Detail endpoint called unexpectedly for rejected ID: {url}")

        mock_get.side_effect = fake_get
        mock_post.return_value = _mock_response({
            "config": {"iiif_url": "https://www.artic.edu/iiif/2"},
            "data": [{
                "id": 700004,
                "title": "AIC Item 4",
                "date_display": "350 CE",
                "date_start": 350,
                "date_end": 350,
                "main_reference_number": "1990.4",
                "image_id": "img-700004",
                "is_public_domain": True,
            }],
        })

        search_res = client.post("/admin/discovery/search", json={
            "museums": ["met", "cma", "aic", "vam"],
            "keywords": ["glass"],
            "date_start": 0,
            "date_end": 899,
            "limit_per_museum": 5,
        })
        assert search_res.status_code == 200
        body = search_res.json()
        assert body["total_new"] == 0
        assert body["total_rejected_skipped"] == 5

    @patch("src.services.museum_discovery_service.requests.get")
    def test_directDiscoveryRejectAndUndo204_togglesSearchSkip(self, mock_get, client):
        # Arrange
        _login_admin(client)
        mock_get.return_value = _mock_response({
            "data": [{
                "id": 199001,
                "accession_number": "1985.12",
                "title": "Blown Glass Unguentarium",
                "creation_date": "2nd–3rd century CE",
                "creation_date_earliest": 100,
                "creation_date_latest": 299,
                "url": "https://clevelandart.org/art/1985.12",
                "images": {"web": {"url": "https://openaccess-cdn.clevelandart.org/1985.12/web.jpg"}},
            }]
        })

        # Act 1: Reject directly from Discovery results
        rej_res = client.post("/admin/discovery/reject", json={
            "candidates": [{
                "museum_id": "cma",
                "source_record_id": "199001",
                "inventory_number": "1985.12",
                "external_url": "https://clevelandart.org/art/1985.12",
                "object_type": "Blown Glass Unguentarium",
                "present_location": "The Cleveland Museum of Art, Cleveland",
                "date_display": "2nd–3rd century CE",
            }]
        })
        assert rej_res.status_code == 200
        rej_data = rej_res.json()
        assert rej_data["rejected_count"] == 1
        assert rej_data["already_rejected_count"] == 0
        rejected_id = rej_data["rejected_items"][0]["id"]

        # Assert 1: Next search skips rejected CMA record
        search1 = client.post("/admin/discovery/search", json={
            "museums": ["cma"],
            "keywords": ["glass"],
            "date_start": 0,
            "date_end": 899,
            "limit_per_museum": 5,
        }).json()
        assert search1["total_new"] == 0
        assert search1["total_rejected_skipped"] == 1

        # Act 2: Undo direct rejection (HTTP 204 empty body)
        undo_res = client.delete(f"/admin/discovery/rejected/{rejected_id}")
        assert undo_res.status_code == 204
        assert undo_res.content == b""

        # Assert 2: Candidate is discoverable again
        search2 = client.post("/admin/discovery/search", json={
            "museums": ["cma"],
            "keywords": ["glass"],
            "date_start": 0,
            "date_end": 899,
            "limit_per_museum": 5,
        }).json()
        assert search2["total_new"] == 1
        assert search2["total_rejected_skipped"] == 0

    @patch("src.services.museum_discovery_service.requests.get")
    def test_edge_reviewUndoRemovesTombstoneIdempotentRejectPaginationAndPublicExclusion(
        self, mock_get, client
    ):
        # Arrange: seed pending object and test Review Queue reject -> undo -> public exclusion
        from src.models import RejectedArtifact

        _login_admin(client)
        db = TestingSessionLocal()
        try:
            pending_obj = Object(
                object_type="Undoable Glass Cup",
                present_location="The Metropolitan Museum of Art, New York",
                findspot="Rome",
                latitude=41.9,
                longitude=12.5,
                date_display="200 CE",
                date_start=200,
                date_end=200,
                inventory_number="MET-UNDO-1",
                external_url="https://www.metmuseum.org/art/collection/search/888001",
                review_status="pending",
            )
            db.add(pending_obj)
            db.commit()
            obj_id = pending_obj.id
        finally:
            db.close()

        # Reject -> tombstone exists & excluded from public search/map/pending
        assert client.patch(f"/objects/{obj_id}/review", json={"status": "rejected"}).status_code == 200
        assert all(o["id"] != obj_id for o in client.get("/objects/search").json())
        assert all(o["id"] != obj_id for o in client.get("/objects/map").json())
        assert all(o["id"] != obj_id for o in client.get("/objects/pending").json())

        db = TestingSessionLocal()
        try:
            assert db.query(RejectedArtifact).filter(RejectedArtifact.source_record_id == "888001").count() == 1
        finally:
            db.close()

        # Undo in Review Queue -> tombstone removed and back in pending queue
        assert client.patch(f"/objects/{obj_id}/review", json={"status": "pending"}).status_code == 200
        db = TestingSessionLocal()
        try:
            assert db.query(RejectedArtifact).filter(RejectedArtifact.source_record_id == "888001").count() == 0
        finally:
            db.close()
        assert any(o["id"] == obj_id for o in client.get("/objects/pending").json())

        # Duplicate direct reject is idempotent
        dup_payload = {
            "candidates": [{
                "museum_id": "cma",
                "source_record_id": "900001",
                "inventory_number": "1999.1",
                "external_url": "https://clevelandart.org/art/1999.1",
                "object_type": "Rejected CMA Piece",
                "date_display": "100 CE",
            }]
        }
        assert client.post("/admin/discovery/reject", json=dup_payload).json()["rejected_count"] == 1
        dup_res = client.post("/admin/discovery/reject", json=dup_payload).json()
        assert dup_res["rejected_count"] == 0
        assert dup_res["already_rejected_count"] == 1

        # Reject 6 Met IDs and 4 CMA IDs so page 1 is completely rejected -> adapter advances to page 2
        met_reject_payload = {
            "candidates": [
                {"museum_id": "met", "source_record_id": str(oid), "object_type": f"Met Rej {oid}"}
                for oid in range(910001, 910007)
            ]
            + [
                {"museum_id": "cma", "source_record_id": str(cid), "inventory_number": f"CMA-R-{cid}", "object_type": f"CMA Rej {cid}"}
                for cid in range(920001, 920005)
            ]
        }
        assert client.post("/admin/discovery/reject", json=met_reject_payload).status_code == 200

        def paginated_get(url, params=None, headers=None, timeout=10):
            if "metmuseum.org/public/collection/v1.1/search" in url:
                offset = (params or {}).get("offset", 0)
                if offset == 0:
                    return _mock_response({"objectIDs": list(range(910001, 910007))})
                return _mock_response({"objectIDs": [910007]})
            if url.endswith("/objects/910007"):
                return _mock_response({
                    "objectID": 910007,
                    "isPublicDomain": True,
                    "accessionNumber": "99.107",
                    "title": "Fresh Page 2 Met Lamp",
                    "objectDate": "300 CE",
                    "objectBeginDate": 300,
                    "objectEndDate": 300,
                    "objectURL": "https://www.metmuseum.org/art/collection/search/910007",
                    "primaryImage": "https://images.metmuseum.org/CRDImages/md/original/fresh.jpg",
                })
            if "openaccess-api.clevelandart.org" in url:
                skip = (params or {}).get("skip", 0)
                if skip == 0:
                    return _mock_response({
                        "data": [
                            {
                                "id": cid,
                                "accession_number": f"CMA-R-{cid}",
                                "title": f"CMA Rej {cid}",
                                "creation_date": "200 CE",
                                "creation_date_earliest": 200,
                                "creation_date_latest": 200,
                                "images": {"web": {"url": f"https://openaccess-cdn.clevelandart.org/{cid}/web.jpg"}},
                            }
                            for cid in range(920001, 920005)
                        ]
                    })
                return _mock_response({
                    "data": [{
                        "id": 920005,
                        "accession_number": "CMA-FRESH-5",
                        "title": "Fresh Page 2 CMA Bowl",
                        "creation_date": "250 CE",
                        "creation_date_earliest": 250,
                        "creation_date_latest": 250,
                        "url": "https://clevelandart.org/art/CMA-FRESH-5",
                        "images": {"web": {"url": "https://openaccess-cdn.clevelandart.org/920005/web.jpg"}},
                    }]
                })
            raise AssertionError(f"Unexpected URL: {url}")

        mock_get.side_effect = paginated_get
        paged_res = client.post("/admin/discovery/search", json={
            "museums": ["met", "cma"],
            "keywords": ["lamp"],
            "date_start": 0,
            "date_end": 899,
            "limit_per_museum": 2,
        })
        assert paged_res.status_code == 200
        paged_data = paged_res.json()
        assert paged_data["total_new"] == 2
        assert paged_data["total_rejected_skipped"] == 10
        titles = {c["object_type"] for c in paged_data["candidates"]}
        assert titles == {"Fresh Page 2 Met Lamp", "Fresh Page 2 CMA Bowl"}

    def test_extraordinary_rejectAuthValidationAndNotFoundErrors(self, client):
        # Act 1: Unauthenticated -> 401
        assert client.post("/admin/discovery/reject", json={
            "candidates": [{"museum_id": "met", "source_record_id": "123"}]
        }).status_code == 401
        assert client.delete("/admin/discovery/rejected/1").status_code == 401

        # Act 2: Non-admin -> 403
        import bcrypt

        db = TestingSessionLocal()
        try:
            hashed = bcrypt.hashpw("UserPass!2026".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            db.add(User(email="viewer@example.com", username="viewer", password_hash=hashed, is_admin=False))
            db.commit()
        finally:
            db.close()
        assert client.post("/auth/login", json={"username": "viewer", "password": "UserPass!2026"}).status_code == 200
        assert client.post("/admin/discovery/reject", json={
            "candidates": [{"museum_id": "met", "source_record_id": "123"}]
        }).status_code == 403
        assert client.delete("/admin/discovery/rejected/1").status_code == 403

        # Act 3: Admin invalid payloads -> 422; missing/zero ID -> 404
        _login_admin(client)
        assert client.post("/admin/discovery/reject", json={"candidates": []}).status_code == 422
        assert client.post("/admin/discovery/reject", json={
            "candidates": [{"museum_id": "invalid_museum", "source_record_id": "123"}]
        }).status_code == 422
        assert client.post("/admin/discovery/reject", json={
            "candidates": [{"museum_id": "met", "source_record_id": "   "}]
        }).status_code == 422
        assert client.post("/admin/discovery/reject", json={
            "candidates": [{"museum_id": "met", "source_record_id": "123", "external_url": "http://insecure.example.com/1"}]
        }).status_code == 422
        assert client.delete("/admin/discovery/rejected/0").status_code == 404
        assert client.delete("/admin/discovery/rejected/99999").status_code == 404



class TestBritishMuseumAdapterDetails:
    """Dedicated Normal, Edge, and Extraordinary tests for BritishMuseumAdapter and BM recovery."""

    def test_wikibaseTimeAndDates_normalAndEdgePrecisions_parseAccurately(self):
        # Arrange
        from src.services.museum_discovery_service import BritishMuseumAdapter

        # Act & Assert: Century precision (7) CE & BCE
        assert BritishMuseumAdapter._parse_wikibase_time(
            {"time": "+0400-01-01T00:00:00Z", "precision": 7}
        ) == (301, 400, "4th century CE")
        assert BritishMuseumAdapter._parse_wikibase_time(
            {"time": "-0400-01-01T00:00:00Z", "precision": 7}
        ) == (-400, -301, "4th century BCE")

        # Decade precision (8) CE & BCE
        assert BritishMuseumAdapter._parse_wikibase_time(
            {"time": "+0320-01-01T00:00:00Z", "precision": 8}
        ) == (320, 329, "320s CE")
        assert BritishMuseumAdapter._parse_wikibase_time(
            {"time": "-0320-01-01T00:00:00Z", "precision": 8}
        ) == (-329, -320, "320s BCE")

        # Year precision (9), including boundary year 0 CE
        assert BritishMuseumAdapter._parse_wikibase_time(
            {"time": "+0000-01-01T00:00:00Z", "precision": 9}
        ) == (0, 0, "0 CE")
        assert BritishMuseumAdapter._parse_wikibase_time(
            {"time": "-0196-01-01T00:00:00Z", "precision": 9}
        ) == (-196, -196, "196 BCE")

        # Millennium precision (6)
        assert BritishMuseumAdapter._parse_wikibase_time(
            {"time": "+0500-01-01T00:00:00Z", "precision": 6}
        ) == (1, 1000, "1st millennium CE")

        # P571 somevalue with P1319 / P1326 + P1480 circa qualifier
        circa_claims = {
            "P571": [{
                "rank": "normal",
                "mainsnak": {"snaktype": "somevalue"},
                "qualifiers": {
                    "P1319": [{"snaktype": "value", "datavalue": {"type": "time", "value": {"time": "+0150-01-01T00:00:00Z", "precision": 9}}}],
                    "P1326": [{"snaktype": "value", "datavalue": {"type": "time", "value": {"time": "+0250-01-01T00:00:00Z", "precision": 9}}}],
                    "P1480": [{"snaktype": "value", "datavalue": {"type": "wikibase-entityid", "value": {"id": "Q5727902"}}}],
                },
            }]
        }
        assert BritishMuseumAdapter._parse_dates(circa_claims) == (150, 250, "c. 150–250 CE")

        # Fallback to P580 / P582 start/end time
        span_claims = {
            "P580": [{"rank": "normal", "mainsnak": {"snaktype": "value", "datavalue": {"type": "time", "value": {"time": "+0300-01-01T00:00:00Z", "precision": 9}}}}],
            "P582": [{"rank": "normal", "mainsnak": {"snaktype": "value", "datavalue": {"type": "time", "value": {"time": "+0450-01-01T00:00:00Z", "precision": 9}}}}],
        }
        assert BritishMuseumAdapter._parse_dates(span_claims) == (300, 450, "300–450 CE")

    @patch("src.services.museum_discovery_service.requests.get")
    def test_bmFilteringAndSanitization_edgeNonArtifactsOutOfRangeAndDeprecatedSkipped(self, mock_get, client):
        # Arrange
        _login_admin(client)

        def fake_get(url, params=None, headers=None, timeout=10):
            params = params or {}
            if "www.wikidata.org/w/api.php" in url and params.get("list") == "search":
                # Special CirrusSearch chars must be stripped from srsearch
                sr = params.get("srsearch", "")
                assert "OR:" not in sr
                assert "(" not in sr
                assert "gold" in sr
                return _mock_response({
                    "query": {
                        "search": [
                            {"title": "Q111"},  # Q5 human -> excluded
                            {"title": "Q222"},  # Out-of-range 1800 CE -> excluded
                            {"title": "Q333"},  # Valid 0 CE artifact
                        ]
                    }
                })
            if "www.wikidata.org/w/api.php" in url and "claims" in params.get("props", ""):
                return _mock_response({
                    "entities": {
                        "Q111": {
                            "id": "Q111",
                            "labels": {"en": {"value": "Roman Potter Person"}},
                            "claims": {
                                "P31": [{"rank": "normal", "mainsnak": {"snaktype": "value", "datavalue": {"type": "wikibase-entityid", "value": {"id": "Q5"}}}}],
                                "P571": [{"rank": "normal", "mainsnak": {"snaktype": "value", "datavalue": {"type": "time", "value": {"time": "+0100-01-01T00:00:00Z", "precision": 9}}}}],
                                "P18": [{"rank": "normal", "mainsnak": {"snaktype": "value", "datavalue": {"type": "string", "value": "Human.jpg"}}}],
                            },
                        },
                        "Q222": {
                            "id": "Q222",
                            "labels": {"en": {"value": "Victorian Teacup"}},
                            "claims": {
                                "P31": [{"rank": "normal", "mainsnak": {"snaktype": "value", "datavalue": {"type": "wikibase-entityid", "value": {"id": "Q220659"}}}}],
                                "P571": [{"rank": "normal", "mainsnak": {"snaktype": "value", "datavalue": {"type": "time", "value": {"time": "+1850-01-01T00:00:00Z", "precision": 9}}}}],
                                "P18": [{"rank": "normal", "mainsnak": {"snaktype": "value", "datavalue": {"type": "string", "value": "Teacup.jpg"}}}],
                            },
                        },
                        "Q333": {
                            "id": "Q333",
                            "labels": {"en": {"value": "Roman Gold-Glass Vessel"}},
                            "claims": {
                                "P31": [{"rank": "normal", "mainsnak": {"snaktype": "value", "datavalue": {"type": "wikibase-entityid", "value": {"id": "Q220659"}}}}],
                                "P571": [
                                    {"rank": "deprecated", "mainsnak": {"snaktype": "value", "datavalue": {"type": "time", "value": {"time": "+1900-01-01T00:00:00Z", "precision": 9}}}},
                                    {"rank": "preferred", "mainsnak": {"snaktype": "value", "datavalue": {"type": "time", "value": {"time": "+0000-01-01T00:00:00Z", "precision": 9}}}},
                                ],
                                "P18": [{"rank": "normal", "mainsnak": {"snaktype": "value", "datavalue": {"type": "string", "value": "Gold glass 0CE.jpg"}}}],
                            },
                        },
                    }
                })
            if "www.wikidata.org/w/api.php" in url:
                return _mock_response({
                    "entities": {
                        "Q220659": {"id": "Q220659", "labels": {"en": {"value": "archaeological artifact"}}},
                    }
                })
            if "commons.wikimedia.org/w/api.php" in url:
                return _mock_response({
                    "query": {
                        "pages": {
                            "5": {
                                "title": "File:Gold glass 0CE.jpg",
                                "imageinfo": [{
                                    "url": "https://upload.wikimedia.org/wikipedia/commons/5/55/Gold_glass_0CE.jpg",
                                    "thumburl": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/55/Gold_glass_0CE.jpg/1000px-Gold_glass_0CE.jpg",
                                }],
                            }
                        }
                    }
                })
            raise AssertionError(f"Unexpected GET URL: {url}")

        mock_get.side_effect = fake_get

        # Act
        res = client.post("/admin/discovery/search", json={
            "museums": ["bm"],
            "keywords": ['"gold" (OR:1)'],
            "date_start": 0,
            "date_end": 899,
            "limit_per_museum": 5,
        })

        # Assert
        assert res.status_code == 200
        data = res.json()
        assert data["total_new"] == 1
        cand = data["candidates"][0]
        assert cand["source_record_id"] == "Q333"
        assert cand["date_start"] == 0
        assert cand["date_end"] == 0
        assert cand["date_display"] == "0 CE"
        assert cand["external_url"] == "https://www.wikidata.org/wiki/Q333"

    @patch("src.services.museum_discovery_service.download_and_store_image", return_value=None)
    def test_bmImportWhenBucketFails_stagesPendingAndPreservesWikimediaUrl(self, _mock_store, client):
        # Arrange
        _login_admin(client)
        wikimedia_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Vindolanda_stylus_BM.jpg/1000px-Vindolanda_stylus_BM.jpg"
        candidate = {
            "museum_id": "bm",
            "museum_name": "The British Museum",
            "source_record_id": "Q2457011",
            "object_type": "Vindolanda Copper-Alloy Stylus",
            "present_location": "The British Museum, London",
            "inventory_number": "1986,1001.15",
            "date_display": "2nd century CE",
            "date_start": 101,
            "date_end": 200,
            "external_url": "https://www.britishmuseum.org/collection/object/H_1986-1001-15",
            "images": [{
                "file_url": wikimedia_url,
                "image_sequence": 1,
                "source_identifier": "BM Q2457011 / File:Vindolanda_stylus_BM.jpg",
            }],
        }

        # Act
        imp = client.post("/admin/discovery/import", json={"candidates": [candidate]})
        assert imp.status_code == 200
        assert imp.json()["imported_count"] == 1

        pending = client.get("/objects/pending").json()
        imported = next(item for item in pending if item["inventory_number"] == "1986,1001.15")

        # Assert
        assert imported["review_status"] == "pending"
        assert imported["images"][0]["file_url"] == wikimedia_url

    @patch("src.services.museum_discovery_service.requests.get")
    @patch("src.services.museum_discovery_service.download_and_store_image", return_value=None)
    def test_recoverObjectImages_bmCommonsAndWikidataPaths_recoversSafely(self, _mock_store, mock_get, client):
        # Arrange: seed two pending BM objects (one with source_identifier File:, one with Wikidata external_url)
        _login_admin(client)
        db = TestingSessionLocal()
        try:
            obj_commons = Object(
                object_type="BM Glass Cup",
                present_location="The British Museum, London",
                date_display="4th century CE",
                date_start=301,
                date_end=400,
                inventory_number="BM-REC-1",
                review_status="pending",
            )
            obj_wikidata = Object(
                object_type="BM Silver Spoon",
                present_location="The British Museum, London",
                date_display="4th century CE",
                date_start=301,
                date_end=400,
                inventory_number="BM-REC-2",
                external_url="https://www.wikidata.org/wiki/Q777888",
                review_status="pending",
            )
            db.add_all([obj_commons, obj_wikidata])
            db.flush()
            db.add_all([
                Image(
                    object_id=obj_commons.id,
                    image_sequence=1,
                    source_identifier="BM Q2457011 / File:Glass_cup.jpg",
                    file_url="",
                ),
                Image(
                    object_id=obj_wikidata.id,
                    image_sequence=1,
                    file_url="",
                ),
            ])
            db.commit()
            id_commons = obj_commons.id
            id_wikidata = obj_wikidata.id
        finally:
            db.close()

        def fake_get(url, params=None, headers=None, timeout=10):
            if "commons.wikimedia.org/w/api.php" in url:
                titles = (params or {}).get("titles", "")
                if "Glass_cup.jpg" in titles:
                    return _mock_response({
                        "query": {
                            "pages": {
                                "1": {
                                    "title": "File:Glass cup.jpg",
                                    "imageinfo": [{"thumburl": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/11/Glass_cup.jpg/1000px-Glass_cup.jpg"}],
                                }
                            }
                        }
                    })
                return _mock_response({
                    "query": {
                        "pages": {
                            "2": {
                                "title": "File:Silver spoon.jpg",
                                "imageinfo": [{"thumburl": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/22/Silver_spoon.jpg/1000px-Silver_spoon.jpg"}],
                            }
                        }
                    }
                })
            if "www.wikidata.org/w/api.php" in url:
                return _mock_response({
                    "entities": {
                        "Q777888": {
                            "id": "Q777888",
                            "claims": {
                                "P18": [{"rank": "normal", "mainsnak": {"snaktype": "value", "datavalue": {"type": "string", "value": "Silver_spoon.jpg"}}}]
                            },
                        }
                    }
                })
            raise AssertionError(f"Unexpected GET URL: {url}")

        mock_get.side_effect = fake_get

        # Act
        res1 = client.post(f"/objects/{id_commons}/recover-images")
        res2 = client.post(f"/objects/{id_wikidata}/recover-images")

        # Assert
        assert res1.status_code == 200
        assert res1.json()["images"][0]["file_url"] == "https://upload.wikimedia.org/wikipedia/commons/thumb/1/11/Glass_cup.jpg/1000px-Glass_cup.jpg"
        assert res2.status_code == 200
        assert res2.json()["images"][0]["file_url"] == "https://upload.wikimedia.org/wikipedia/commons/thumb/2/22/Silver_spoon.jpg/1000px-Silver_spoon.jpg"

    @patch("src.services.museum_discovery_service.requests.post")
    @patch("src.services.museum_discovery_service.requests.get")
    def test_bmExtraordinaryTimeoutAndUntrustedImageHosts_handledSafely(self, mock_get, mock_post, client):
        # Arrange: Wikidata times out while AIC succeeds
        _login_admin(client)
        mock_get.side_effect = requests.Timeout("Wikidata timeout")
        mock_post.return_value = _mock_response({
            "config": {"iiif_url": "https://www.artic.edu/iiif/2"},
            "data": [{
                "id": 888,
                "title": "Roman Lamp",
                "date_display": "200 CE",
                "date_start": 200,
                "date_end": 200,
                "main_reference_number": "1950.88",
                "image_id": "img-888",
                "is_public_domain": True,
            }],
        })

        # Act 1: Partial failure degrades cleanly
        search_res = client.post("/admin/discovery/search", json={
            "museums": ["bm", "aic"],
            "keywords": ["lamp"],
            "date_start": 0,
            "date_end": 899,
            "limit_per_museum": 5,
        })
        assert search_res.status_code == 200
        reports = {r["museum_id"]: r for r in search_res.json()["museum_reports"]}
        assert "Wikidata timeout" in reports["bm"]["error"]
        assert reports["aic"]["new_count"] == 1

        # Act 2 & Assert: Non-HTTPS or lookalike upload.wikimedia.org host rejected with 422 on import
        for bad_url in (
            "http://upload.wikimedia.org/wikipedia/commons/a/ab/Test.jpg",
            "https://upload.wikimedia.org.evil.com/Test.jpg",
        ):
            imp_res = client.post("/admin/discovery/import", json={
                "candidates": [{
                    "museum_id": "bm",
                    "museum_name": "The British Museum",
                    "source_record_id": "Q999",
                    "object_type": "Bad URL Piece",
                    "date_display": "200 CE",
                    "date_start": 200,
                    "date_end": 200,
                    "images": [{"file_url": bad_url, "image_sequence": 1}],
                }]
            })
            assert imp_res.status_code == 422

    @patch("src.services.museum_discovery_service.requests.get")
    def test_bmRejectedArtifact_skipsInPhase1BeforeDetailFetchAndExtractsProvenance(self, mock_get, client):
        # Arrange: reject a BM candidate via /admin/discovery/reject
        _login_admin(client)
        from src.services.rejection_service import extract_museum_provenance

        rej_res = client.post("/admin/discovery/reject", json={
            "candidates": [{
                "museum_id": "bm",
                "source_record_id": "Q2457011",
                "inventory_number": "1986,1001.15",
                "external_url": "https://www.britishmuseum.org/collection/object/H_1986-1001-15",
                "object_type": "Vindolanda Copper-Alloy Stylus",
                "present_location": "The British Museum, London",
                "date_display": "2nd century CE",
            }]
        })
        assert rej_res.status_code == 200
        assert rej_res.json()["rejected_count"] == 1

        called_actions = []

        def fake_get(url, params=None, headers=None, timeout=10):
            params = params or {}
            called_actions.append(params.get("list") or params.get("action"))
            if "www.wikidata.org/w/api.php" in url and params.get("list") == "search":
                return _mock_response({"query": {"search": [{"title": "Q2457011"}]}})
            raise AssertionError(f"Unexpected detail fetch for rejected BM artifact: {url} params={params}")

        mock_get.side_effect = fake_get

        # Act: run discovery search for bm -> Q2457011 must be skipped in Phase 1
        search_res = client.post("/admin/discovery/search", json={
            "museums": ["bm"],
            "keywords": ["stylus"],
            "date_start": 0,
            "date_end": 899,
            "limit_per_museum": 5,
        })

        # Assert
        assert search_res.status_code == 200
        data = search_res.json()
        assert data["total_new"] == 0
        assert data["total_duplicates_skipped"] >= 1
        assert data["total_rejected_skipped"] >= 1
        assert called_actions == ["search"]

        # Assert Wikidata Q-ID extraction in extract_museum_provenance
        assert extract_museum_provenance(
            external_url="https://www.britishmuseum.org/collection/object/H_1986-1001-15",
            source_identifiers=["BM Q2457011 / File:Foo.jpg"],
        ) == ("bm", "Q2457011")
        assert extract_museum_provenance(
            external_url="https://www.wikidata.org/wiki/Q2457011",
            present_location="The British Museum, London",
        ) == ("bm", "Q2457011")


class TestWorkerDepictionDiscoveryMode:
    """Normal, Edge, and Extraordinary tests for ancient worker depiction discovery mode & presets."""

    def test_presetsEndpoint_authAndStructure_returnsFiveWorkerPresets(self, client):
        # Arrange / Act: unauthenticated rejected
        assert client.get("/admin/discovery/presets").status_code == 401

        # Authenticate admin & fetch presets
        _login_admin(client)
        res = client.get("/admin/discovery/presets")

        # Assert
        assert res.status_code == 200
        presets = res.json()
        assert len(presets) == 5
        ids = {p["id"] for p in presets}
        assert "all_ancient_workers" in ids
        assert "artisans_workshops" in ids
        for p in presets:
            assert p["keywords"]
            assert p["recommended_date_start"] <= p["recommended_date_end"]

    @patch("src.services.museum_discovery_service.requests.post")
    @patch("src.services.museum_discovery_service.requests.get")
    def test_workerDepictionsMode_filtersNoiseUsesDepictionQueriesAndSkipsSavingPresetKeywords(
        self, mock_get, mock_post, client
    ):
        # Arrange
        _login_admin(client)
        met_search_params = []
        vam_search_params = []
        bm_search_queries = []
        aic_requests = []

        def fake_get(url, params=None, headers=None, timeout=10):
            params = params or {}
            if "collectionapi.metmuseum.org/public/collection/v1.1/search" in url:
                met_search_params.append(dict(params))
                if params.get("tags") == "true" and params.get("q") == "Bakers":
                    return _mock_response({"objectIDs": [880001, 880002]})
                return _mock_response({"objectIDs": []})
            if url.endswith("/objects/880001"):
                return _mock_response({
                    "objectID": 880001,
                    "isPublicDomain": True,
                    "accessionNumber": "20.3.12",
                    "title": "Model of a Bakery and Brewery",
                    "objectName": "Tomb model",
                    "medium": "Painted wood",
                    "objectDate": "ca. 1981–1975 BCE",
                    "objectBeginDate": -1981,
                    "objectEndDate": -1975,
                    "objectURL": "https://www.metmuseum.org/art/collection/search/880001",
                    "primaryImage": "https://images.metmuseum.org/CRDImages/eg/original/bakery.jpg",
                    "tags": [{"term": "Bakers"}, {"term": "Brewing"}],
                })
            if url.endswith("/objects/880002"):
                return _mock_response({
                    "objectID": 880002,
                    "isPublicDomain": True,
                    "accessionNumber": "91.1.1",
                    "title": "Roman Mold-Blown Glass Bottle",
                    "objectName": "Bottle",
                    "medium": "Mold-blown glass",
                    "objectDate": "2nd century CE",
                    "objectBeginDate": 100,
                    "objectEndDate": 199,
                    "objectURL": "https://www.metmuseum.org/art/collection/search/880002",
                    "primaryImage": "https://images.metmuseum.org/CRDImages/gr/original/bottle.jpg",
                    "tags": [],
                })
            if "openaccess-api.clevelandart.org" in url:
                if params.get("q") == "scribe":
                    return _mock_response({
                        "data": [
                            {
                                "id": 880003,
                                "accession_number": "1988.10",
                                "title": "Wall Relief of Scribes Weighing Gold",
                                "type": "Relief",
                                "creation_date": "1350 BCE",
                                "creation_date_earliest": -1350,
                                "creation_date_latest": -1340,
                                "did_you_know": "Depicting royal scribes recording weight in grain.",
                                "url": "https://clevelandart.org/art/1988.10",
                                "images": {"web": {"url": "https://openaccess-cdn.clevelandart.org/1988.10/web.jpg"}},
                            },
                            {
                                "id": 880004,
                                "accession_number": "1988.11",
                                "title": "Terracotta Neck-Amphora Attributed to the Antimenes Painter",
                                "type": "Vessel",
                                "description": "Wheel-thrown ceramic vase with openwork rim.",
                                "creation_date": "520 BCE",
                                "creation_date_earliest": -520,
                                "creation_date_latest": -510,
                                "url": "https://clevelandart.org/art/1988.11",
                                "images": {"web": {"url": "https://openaccess-cdn.clevelandart.org/1988.11/web.jpg"}},
                            },
                        ]
                    })
                return _mock_response({"data": []})
            if "api.vam.ac.uk/v2/objects/search" in url:
                vam_search_params.append(dict(params))
                if params.get("q_object_title") == "weaver":
                    return _mock_response({
                        "records": [
                            {"systemNumber": "O880007", "accessionNumber": "V.1"},
                            {"systemNumber": "O880008", "accessionNumber": "V.2"},
                        ]
                    })
                return _mock_response({"records": []})
            if "api.vam.ac.uk/v2/museumobject/O880007" in url:
                return _mock_response({
                    "record": {
                        "systemNumber": "O880007",
                        "accessionNumber": "V.1",
                        "objectType": "Relief",
                        "titles": [{"title": "Weaver at an Upright Loom Relief"}],
                        "summaryDescription": "Carved plaque depicting women weaving cloth.",
                        "productionDates": [{"date": {"text": "3rd century CE", "earliest": "0200", "latest": "0299"}}],
                        "images": ["img-weaver"],
                        "contentPerson": [{"name": "Weaver"}],
                        "categories": [{"text": "Weaving"}],
                    }
                })
            if "api.vam.ac.uk/v2/museumobject/O880008" in url:
                return _mock_response({
                    "record": {
                        "systemNumber": "O880008",
                        "accessionNumber": "V.2",
                        "objectType": "Saw",
                        "titles": [{"title": "Iron Saw"}],
                        "briefDescription": "Heavy iron carpenter's saw blade.",
                        "productionDates": [{"date": {"text": "2nd century CE", "earliest": "0100", "latest": "0199"}}],
                        "images": ["img-saw"],
                        "categories": [{"text": "Tools"}],
                    }
                })
            if "www.wikidata.org/w/api.php" in url:
                if params.get("list") == "search":
                    sr = params.get("srsearch", "")
                    bm_search_queries.append(sr)
                    if "haswbstatement:P180" in sr and "shoemaker" in sr:
                        return _mock_response({"query": {"search": [{"title": "Q880009"}, {"title": "Q880010"}]}})
                    return _mock_response({"query": {"search": []}})
                if params.get("action") == "wbgetentities" and "claims" in params.get("props", ""):
                    return _mock_response({
                        "entities": {
                            "Q880009": {
                                "id": "Q880009",
                                "labels": {"en": {"value": "Grave Stele of Xanthippos"}},
                                "descriptions": {"en": {"value": "Athenian marble funerary stele depicting a seated shoemaker"}},
                                "claims": {
                                    "P31": [{"rank": "normal", "mainsnak": {"snaktype": "value", "datavalue": {"type": "wikibase-entityid", "value": {"id": "Q178743"}}}}],
                                    "P180": [{"rank": "normal", "mainsnak": {"snaktype": "value", "datavalue": {"type": "wikibase-entityid", "value": {"id": "Q152355"}}}}],
                                    "P571": [{"rank": "normal", "mainsnak": {"snaktype": "value", "datavalue": {"type": "time", "value": {"time": "-0420-01-01T00:00:00Z", "precision": 8}}}}],
                                    "P18": [{"rank": "normal", "mainsnak": {"snaktype": "value", "datavalue": {"type": "string", "value": "Xanthippos_stele.jpg"}}}],
                                },
                            },
                            "Q880010": {
                                "id": "Q880010",
                                "labels": {"en": {"value": "Writing Stylus"}},
                                "descriptions": {"en": {"value": "Bronze writing stylus"}},
                                "claims": {
                                    "P31": [{"rank": "normal", "mainsnak": {"snaktype": "value", "datavalue": {"type": "wikibase-entityid", "value": {"id": "Q500100"}}}}],
                                    "P571": [{"rank": "normal", "mainsnak": {"snaktype": "value", "datavalue": {"type": "time", "value": {"time": "+0200-01-01T00:00:00Z", "precision": 7}}}}],
                                    "P18": [{"rank": "normal", "mainsnak": {"snaktype": "value", "datavalue": {"type": "string", "value": "Stylus_bm.jpg"}}}],
                                },
                            },
                        }
                    })
                if params.get("action") == "wbgetentities":
                    return _mock_response({
                        "entities": {
                            "Q178743": {"id": "Q178743", "labels": {"en": {"value": "stele"}}},
                            "Q152355": {"id": "Q152355", "labels": {"en": {"value": "shoemaker"}}},
                            "Q500100": {"id": "Q500100", "labels": {"en": {"value": "stylus"}}},
                        }
                    })
            if "commons.wikimedia.org/w/api.php" in url:
                return _mock_response({
                    "query": {
                        "normalized": [],
                        "pages": {
                            "1": {
                                "title": "File:Xanthippos_stele.jpg",
                                "imageinfo": [{"url": "https://upload.wikimedia.org/wikipedia/commons/x/xa/Xanthippos_stele.jpg", "extmetadata": {}}],
                            },
                            "2": {
                                "title": "File:Stylus_bm.jpg",
                                "imageinfo": [{"url": "https://upload.wikimedia.org/wikipedia/commons/s/st/Stylus_bm.jpg", "extmetadata": {}}],
                            },
                        },
                    }
                })
            raise AssertionError(f"Unexpected GET URL: {url} params={params}")

        def fake_post(url, json=None, headers=None, timeout=10):
            aic_requests.append({"json": json, "headers": headers})
            query_text = json["query"]["bool"]["must"][0]["multi_match"]["query"]
            if query_text == "potter":
                return _mock_response({
                    "config": {"iiif_url": "https://www.artic.edu/iiif/2"},
                    "data": [
                        {
                            "id": 880005,
                            "title": "Terracotta Neck-Amphora",
                            "artwork_type_title": "Vessel",
                            "date_display": "520 BCE",
                            "date_start": -525,
                            "date_end": -515,
                            "main_reference_number": "1989.5",
                            "subject_titles": ["Harvesting", "Working"],
                            "thumbnail": {"alt_text": "Black-figure amphora depicting farmers harvesting olives"},
                            "image_id": "img-aic-worker",
                            "is_public_domain": True,
                        },
                        {
                            "id": 880006,
                            "title": "Terracotta Loom Weight",
                            "artwork_type_title": "Loom weight",
                            "description": "Clay weight used for weaving cloth.",
                            "date_display": "300 BCE",
                            "date_start": -300,
                            "date_end": -300,
                            "main_reference_number": "1989.6",
                            "subject_titles": [],
                            "image_id": "img-aic-loom",
                            "is_public_domain": True,
                        },
                    ],
                })
            return _mock_response({"config": {"iiif_url": "https://www.artic.edu/iiif/2"}, "data": []})

        mock_get.side_effect = fake_get
        mock_post.side_effect = fake_post

        # Act
        res = client.post("/admin/discovery/search", json={
            "museums": ["met", "cma", "aic", "vam", "bm"],
            "keywords": ["craftsman", "glass", "potter", "scribe", "shoemaker", "weaver", "baker", "xanthippos-unsaved"],
            "date_start": -3000,
            "date_end": 899,
            "limit_per_museum": 5,
            "search_mode": "worker_depictions",
            "min_worker_score": 35,
            "save_keywords": False,
        })

        # Assert API query optimizations
        assert res.status_code == 200
        assert any(p.get("tags") == "true" for p in met_search_params)
        assert all(p.get("q") != "glass" for p in met_search_params)
        assert any(p.get("q_object_title") == "weaver" for p in vam_search_params)
        assert any("haswbstatement:P180" in q for q in bm_search_queries)
        assert aic_requests
        assert "AIC-User-Agent" in (aic_requests[0]["headers"] or {})
        assert "q" not in aic_requests[0]["json"]
        assert "subject_titles^5" in aic_requests[0]["json"]["query"]["bool"]["must"][0]["multi_match"]["fields"]

        # Assert filtering & ranking
        data = res.json()
        assert data["search_mode"] == "worker_depictions"
        assert data["total_new"] == 5
        assert data["total_filtered_non_worker"] >= 5
        scores = [c["worker_relevance_score"] for c in data["candidates"]]
        assert scores == sorted(scores, reverse=True)
        assert all(s >= 35 for s in scores)
        by_museum = {c["museum_id"]: c for c in data["candidates"]}
        assert set(by_museum.keys()) == {"met", "cma", "aic", "vam", "bm"}
        assert "shoemaker" in by_museum["bm"]["tags"]

        # Assert save_keywords=False did NOT persist the transient keyword
        saved_kws = client.get("/admin/discovery/keywords").json()
        assert "xanthippos-unsaved" not in saved_kws

    @patch("src.services.museum_discovery_service.requests.get")
    def test_workerDepictionsMode_filteredItemsNotRegisteredInIndexAndStreamReportsFiltered(
        self, mock_get, client
    ):
        # Arrange: verify direct adapter leaves filtered item unregistered in ExistingArtifactIndex,
        # and verify stream + min_worker_score boundaries
        _login_admin(client)
        from src.services.museum_discovery_service import ExistingArtifactIndex, MetMuseumAdapter

        def fake_get(url, params=None, headers=None, timeout=10):
            if "metmuseum.org/public/collection/v1.1/search" in url:
                return _mock_response({"objectIDs": [890001]})
            if url.endswith("/objects/890001"):
                return _mock_response({
                    "objectID": 890001,
                    "isPublicDomain": True,
                    "accessionNumber": "99.9.1",
                    "title": "Plain Glass Jar",
                    "medium": "Mold-blown glass",
                    "objectBeginDate": 100,
                    "objectEndDate": 200,
                    "objectURL": "https://www.metmuseum.org/art/collection/search/890001",
                    "primaryImage": "https://images.metmuseum.org/CRDImages/gr/original/jar.jpg",
                    "tags": [],
                })
            raise AssertionError(f"Unexpected URL: {url}")

        mock_get.side_effect = fake_get

        # Edge 1: Adapter filters out non-worker without registering in ExistingArtifactIndex
        db = TestingSessionLocal()
        try:
            idx = ExistingArtifactIndex(db)
            kept, fetched, dupes, rej, filtered = MetMuseumAdapter().discover(
                keywords=["glass"],
                date_start=0,
                date_end=899,
                limit=5,
                index=idx,
                search_mode="worker_depictions",
                min_worker_score=35,
            )
            assert kept == []
            assert filtered == 1
            assert idx.contains(museum_id="met", source_record_id="890001") is False
        finally:
            db.close()

        # Edge 2: min_worker_score=0 keeps all items; stream emits filtered_non_worker in worker_depictions mode
        with client.stream("POST", "/admin/discovery/search/stream", json={
            "museums": ["met"],
            "keywords": ["glass"],
            "date_start": 0,
            "date_end": 899,
            "limit_per_museum": 5,
            "search_mode": "worker_depictions",
            "min_worker_score": 35,
        }) as res:
            assert res.status_code == 200
            events = [json.loads(line) for line in res.iter_lines() if line]

        complete_evt = events[-1]
        assert complete_evt["type"] == "complete"
        assert complete_evt["search_mode"] == "worker_depictions"
        assert complete_evt["total_new"] == 0
        assert complete_evt["total_filtered_non_worker"] == 1

        broad_keep = client.post("/admin/discovery/search", json={
            "museums": ["met"],
            "keywords": ["glass"],
            "date_start": 0,
            "date_end": 899,
            "limit_per_museum": 5,
            "search_mode": "worker_depictions",
            "min_worker_score": 0,
        })
        assert broad_keep.status_code == 200
        assert broad_keep.json()["total_new"] == 1

    def test_workerDepictionsMode_extraordinaryInvalidSearchModeAndBounds_return422(self, client):
        # Arrange
        _login_admin(client)

        # Act & Assert
        assert client.post("/admin/discovery/search", json={
            "museums": ["met"],
            "keywords": ["potter"],
            "search_mode": "invalid_mode",
        }).status_code == 422
        assert client.post("/admin/discovery/search", json={
            "museums": ["met"],
            "keywords": ["potter"],
            "min_worker_score": -1,
        }).status_code == 422
        assert client.post("/admin/discovery/search", json={
            "museums": ["met"],
            "keywords": ["potter"],
            "min_worker_score": 101,
        }).status_code == 422
