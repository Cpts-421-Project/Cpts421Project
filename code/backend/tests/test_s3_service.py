"""
Comprehensive unit tests for S3 storage service and bucket image management.
Tests Normal, Edge, and Extraordinary cases using AAA pattern.
Mocks external HTTP requests and Boto3 client interactions.
"""
from unittest.mock import MagicMock, patch
import pytest
from botocore.exceptions import ClientError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.config import config
from src.exceptions import StorageError, ValidationError
from src.models import Base, Object, Image, Tag, Source
from src.services.object_service import ObjectService
from src.services.s3_service import (
    is_bucket_url,
    validate_magic_bytes,
    upload_bytes_to_minio,
    download_and_store_image,
    ensure_stored_in_bucket,
    MAX_FILE_SIZE_BYTES,
)


@pytest.fixture
def mock_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


# =====================================================================
# 1. is_bucket_url Tests
# =====================================================================

class TestIsBucketUrl:
    """Tests for identifying whether an image URL is in our storage bucket."""

    def test_isBucketUrl_normalPublicUrl_returnsTrue(self):
        # Arrange
        url = f"{config.MINIO_PUBLIC_URL}/uploads/manual_12345678.jpg"

        # Act
        result = is_bucket_url(url)

        # Assert
        assert result is True

    def test_isBucketUrl_bucketPathInUrl_returnsTrue(self):
        # Arrange
        url = f"https://storage.railway.app/{config.MINIO_BUCKET}/artifact_001.webp"

        # Act
        result = is_bucket_url(url)

        # Assert
        assert result is True

    def test_isBucketUrl_edgeEmptyOrNone_returnsFalse(self):
        # Arrange & Act & Assert
        assert is_bucket_url("") is False
        assert is_bucket_url(None) is False
        assert is_bucket_url(12345) is False

    def test_isBucketUrl_extraordinaryExternalDomain_returnsFalse(self):
        # Arrange
        url = "https://collectionapi.metmuseum.org/api/collection/v1/iiif/241792/main-image"

        # Act
        result = is_bucket_url(url)

        # Assert
        assert result is False

    def test_isBucketUrl_extraordinarySubdomainAttack_returnsFalse(self):
        # Arrange - bucket name appearing in an untrusted domain name
        url = "https://uploads-malicious.attacker.com/evil.jpg"

        # Act
        result = is_bucket_url(url)

        # Assert
        assert result is False


# =====================================================================
# 2. validate_magic_bytes Tests
# =====================================================================

class TestValidateMagicBytes:
    """Tests for magic byte signature detection and validation."""

    def test_validateMagicBytes_normalJpeg_returnsJpgTuple(self):
        # Arrange
        content = b"\xff\xd8\xff\xe0\x00\x10JFIF"

        # Act
        ext, mime = validate_magic_bytes(content)

        # Assert
        assert ext == "jpg"
        assert mime == "image/jpeg"

    def test_validateMagicBytes_normalPng_returnsPngTuple(self):
        # Arrange
        content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"

        # Act
        ext, mime = validate_magic_bytes(content)

        # Assert
        assert ext == "png"
        assert mime == "image/png"

    def test_validateMagicBytes_normalWebp_returnsWebpTuple(self):
        # Arrange
        content = b"RIFF\x24\x00\x00\x00WEBPVP8 "

        # Act
        ext, mime = validate_magic_bytes(content)

        # Assert
        assert ext == "webp"
        assert mime == "image/webp"

    def test_validateMagicBytes_edgeEmptyContent_raisesValidationError(self):
        # Arrange
        content = b""

        # Act & Assert
        with pytest.raises(ValidationError, match="Empty file payload"):
            validate_magic_bytes(content)

    def test_validateMagicBytes_extraordinaryHtmlPayload_raisesValidationError(self):
        # Arrange: Museum returns an HTML 404 page instead of image bytes
        content = b"<!DOCTYPE html><html><body>404 Not Found</body></html>"

        # Act & Assert
        with pytest.raises(ValidationError, match="does not match any allowed image signature"):
            validate_magic_bytes(content)


# =====================================================================
# 3. upload_bytes_to_minio Tests
# =====================================================================

class TestUploadBytesToMinio:
    """Tests for raw binary upload to S3/MinIO bucket."""

    @patch("src.services.s3_service.get_s3_client")
    def test_uploadBytes_normalJpeg_callsPutObjectAndReturnsUrl(self, mock_client_getter):
        # Arrange
        mock_client = MagicMock()
        mock_client_getter.return_value = mock_client
        jpeg_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 50

        # Act
        url = upload_bytes_to_minio(jpeg_bytes, file_name="test_lamp.jpg")

        # Assert
        assert "test_lamp.jpg" in url
        mock_client.put_object.assert_called_once_with(
            Bucket=config.MINIO_BUCKET,
            Key="test_lamp.jpg",
            Body=jpeg_bytes,
            ContentType="image/jpeg",
        )

    def test_uploadBytes_edgeOversized_raisesValidationError(self):
        # Arrange: 11 MB of data (limit is 10 MB)
        oversized_bytes = b"\xff\xd8\xff" + b"\x00" * (MAX_FILE_SIZE_BYTES + 10)

        # Act & Assert
        with pytest.raises(ValidationError, match="File size exceeds maximum allowed limit"):
            upload_bytes_to_minio(oversized_bytes)

    @patch("src.services.s3_service.get_s3_client")
    def test_uploadBytes_extraordinaryClientError_raisesStorageError(self, mock_client_getter):
        # Arrange
        mock_client = MagicMock()
        mock_client.put_object.side_effect = ClientError(
            {"Error": {"Message": "Access Denied"}}, "PutObject"
        )
        mock_client_getter.return_value = mock_client
        jpeg_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF"

        # Act & Assert
        with pytest.raises(StorageError, match="Cloud storage error: Access Denied"):
            upload_bytes_to_minio(jpeg_bytes, file_name="error_test.jpg")


# =====================================================================
# 4. download_and_store_image & ensure_stored_in_bucket Tests
# =====================================================================

class TestDownloadAndStoreImage:
    """Tests for external image download, validation, and storage piping."""

    @patch("src.services.s3_service.upload_bytes_to_minio")
    @patch("src.services.s3_service.requests.get")
    def test_downloadAndStore_normalMuseumUrl_uploadsToBucket(self, mock_get, mock_upload):
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_content.return_value = [b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01"]
        mock_get.return_value = mock_response
        mock_upload.return_value = f"{config.MINIO_PUBLIC_URL}/{config.MINIO_BUCKET}/obj_lamp_123.jpg"

        url = "https://collectionapi.metmuseum.org/api/collection/v1/iiif/241792/2105480/main-image"

        # Act
        result = download_and_store_image(url, object_identifier="241792")

        # Assert
        assert result == f"{config.MINIO_PUBLIC_URL}/{config.MINIO_BUCKET}/obj_lamp_123.jpg"
        mock_upload.assert_called_once()

    def test_downloadAndStore_edgeAlreadyInBucket_returnsDirectly(self):
        # Arrange
        bucket_url = f"{config.MINIO_PUBLIC_URL}/{config.MINIO_BUCKET}/already_there.jpg"

        # Act
        result = download_and_store_image(bucket_url)

        # Assert: No HTTP call made, returns input URL directly
        assert result == bucket_url

    def test_downloadAndStore_extraordinarySsrfBlockedDomain_returnsNone(self):
        # Arrange: Untrusted/internal domain blocked by allowlist
        malicious_url = "https://169.254.169.254/latest/meta-data/credentials"

        # Act
        result = download_and_store_image(malicious_url)

        # Assert
        assert result is None

    @patch("src.services.s3_service.requests.get")
    def test_downloadAndStore_extraordinaryInvalidContent_returnsNone(self, mock_get):
        # Arrange: Response is an HTML error page, not an image
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_content.return_value = [b"<html>Error</html>"]
        mock_get.return_value = mock_response

        url = "https://collectionapi.metmuseum.org/api/collection/v1/iiif/999999/bad"

        # Act
        result = download_and_store_image(url)

        # Assert
        assert result is None

    @patch("src.services.s3_service.download_and_store_image")
    def test_ensureStoredInBucket_fallbackToOriginalOnFailure(self, mock_download):
        # Arrange
        mock_download.return_value = None
        ext_url = "https://collectionapi.metmuseum.org/api/collection/v1/iiif/fail/main-image"

        # Act
        result = ensure_stored_in_bucket(ext_url)

        # Assert: Graceful degradation, returns original URL
        assert result == ext_url


# =====================================================================
# 5. ObjectService Bucket Enforcement Tests
# =====================================================================

class TestObjectServiceBucketEnforcement:
    """Verifies that ObjectService auto-pipes external images into our bucket on create and update."""

    @patch("src.services.object_service.ensure_stored_in_bucket")
    def test_createObject_withExternalImage_pipesToBucket(self, mock_ensure, mock_db):
        # Arrange
        mock_ensure.return_value = f"{config.MINIO_PUBLIC_URL}/{config.MINIO_BUCKET}/migrated_img.jpg"
        service = ObjectService(mock_db)

        object_data = {
            "object_type": "Terracotta Vessel",
            "inventory_number": "INV-S3-001",
            "date_display": "c. 400 AD",
            "date_start": 350,
            "date_end": 450,
            "images": [
                {
                    "file_url": "https://collectionapi.metmuseum.org/api/collection/v1/iiif/123/main-image",
                    "image_type": "Photograph",
                    "view_type": "Front",
                }
            ],
        }

        # Act
        created = service.create_object(object_data)

        # Assert
        assert len(created["images"]) == 1
        assert created["images"][0].file_url == f"{config.MINIO_PUBLIC_URL}/{config.MINIO_BUCKET}/migrated_img.jpg"
        mock_ensure.assert_called_once()

    @patch("src.services.object_service.ensure_stored_in_bucket")
    def test_updateObject_withExternalImage_pipesToBucket(self, mock_ensure, mock_db):
        # Arrange
        service = ObjectService(mock_db)
        initial_obj = service.create_object({
            "object_type": "Coin",
            "inventory_number": "INV-S3-002",
            "date_display": "c. 500 AD",
            "date_start": 450,
            "date_end": 550,
            "images": [],
        })

        mock_ensure.return_value = f"{config.MINIO_PUBLIC_URL}/{config.MINIO_BUCKET}/updated_img.jpg"

        update_payload = {
            "object_type": "Coin Updated",
            "images": [
                {
                    "file_url": "https://collectionapi.metmuseum.org/api/collection/v1/iiif/456/main-image",
                    "image_type": "Photograph",
                    "view_type": "Front",
                }
            ],
        }

        # Act
        updated = service.update_object(initial_obj["id"], update_payload)

        # Assert
        assert len(updated["images"]) == 1
        assert updated["images"][0].file_url == f"{config.MINIO_PUBLIC_URL}/{config.MINIO_BUCKET}/updated_img.jpg"
