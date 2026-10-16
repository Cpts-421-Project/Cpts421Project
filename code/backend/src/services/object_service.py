"""
Service layer for Object-related business logic.
Sits between API routes (controllers) and the repository layer.
Owns the bibliography aggregation logic that was previously duplicated in 3 places.
"""
import re
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from ..repositories.object_repository import ObjectRepository
from ..models import Object
from ..logger import app_logger
from ..exceptions import EntityNotFoundError, BaseAppException
from .s3_service import ensure_stored_in_bucket


def build_bibliography(obj: Object) -> List[str]:
    """
    Extracts unique citation texts from an object's source-linked images.
    This was previously duplicated in main.py search_objects, get_object_detail,
    and partially in object_repository.get_by_id.
    """
    citations = set()
    for img in obj.images:
        if img.source:
            citations.add(img.source.citation_text)
    return list(citations)


def extract_tags(obj: Object) -> List[str]:
    """Extracts unique tag names associated with an object's images."""
    tags = set()
    for img in getattr(obj, "images", []):
        for t in getattr(img, "tags", []):
            if hasattr(t, "tag_name") and t.tag_name:
                tags.add(t.tag_name)
    return sorted(list(tags))


def _normalize_image_url(url: Optional[str], inventory_number: Optional[str] = None) -> Optional[str]:
    """
    Normalizes any external Met Museum image URL to our internal bucket proxy endpoint.
    Guarantees no external Met URLs are returned to the frontend.
    """
    if not url or not isinstance(url, str):
        return url

    url_lower = url.lower()
    if "metmuseum.org" in url_lower or "collectionapi" in url_lower:
        if inventory_number:
            safe_inv = "".join(c if c.isalnum() else "_" for c in str(inventory_number))
            return f"/api/images/met_{safe_inv}.jpg"
        match = re.search(r"/iiif/([^/]+)/", url)
        if match:
            safe_inv = "".join(c if c.isalnum() else "_" for c in match.group(1))
            return f"/api/images/met_{safe_inv}.jpg"
        return "/api/images/met_default.jpg"

    return url


def _enrich_object_dict(obj: Object) -> dict:
    """Converts an ORM Object to a dict enriched with bibliography and tags data."""
    obj_dict = obj.__dict__.copy()
    obj_dict['bibliography'] = build_bibliography(obj)

    inv_num = getattr(obj, "inventory_number", None)
    for img in getattr(obj, "images", []):
        if hasattr(img, "file_url") and img.file_url:
            img.file_url = _normalize_image_url(img.file_url, inv_num)
        elif isinstance(img, dict) and "file_url" in img:
            img["file_url"] = _normalize_image_url(img["file_url"], inv_num)

    obj_dict['images'] = obj.images
    obj_dict['tags'] = extract_tags(obj)
    return obj_dict


class ObjectService:
    """Encapsulates business logic for artifact queries."""

    def __init__(self, db: Session):
        self.repo = ObjectRepository(db)

    def search(
        self,
        material: Optional[str] = None,
        year: Optional[int] = None,
        date_start: Optional[int] = None,
        date_end: Optional[int] = None,
        search: Optional[str] = None,
        tags: Optional[List[str]] = None,
        tag_mode: str = "any",
        skip: int = 0,
        limit: int = 100,
    ) -> List[dict]:
        """Search objects and enrich each with bibliography and tags."""
        try:
            objects = self.repo.search(
                material=material,
                year=year,
                date_start=date_start,
                date_end=date_end,
                search=search,
                tags=tags,
                tag_mode=tag_mode,
                skip=skip,
                limit=limit
            )
            return [_enrich_object_dict(obj) for obj in objects]
        except SQLAlchemyError as e:
            app_logger.error("Database search failed", exc_info=True)
            raise BaseAppException("Internal database error during search", 500)

    def get_by_id(self, object_id: int) -> Optional[dict]:
        """Fetch a single object by ID, enriched with bibliography."""
        try:
            obj = self.repo.get_by_id(object_id)
            if not obj:
                app_logger.warning("Object not found", extra={"object_id": object_id})
                raise EntityNotFoundError("Object", object_id)
            return _enrich_object_dict(obj)
        except SQLAlchemyError as e:
            app_logger.error("Database GET failed", exc_info=True)
            raise BaseAppException("Internal database error", 500)

    def get_map_data(self) -> List[dict]:
        """Lightweight map data — no enrichment needed."""
        try:
            return self.repo.get_map_data()
        except SQLAlchemyError:
            app_logger.error("Database map data query failed", exc_info=True)
            raise BaseAppException("Internal database error fetching map data", 500)

    def get_all_tags(self) -> List[str]:
        """All unique tag names."""
        try:
            return self.repo.get_all_tags()
        except SQLAlchemyError:
            app_logger.error("Database tags query failed", exc_info=True)
            raise BaseAppException("Internal database error fetching tags", 500)

    def get_pending_objects(self) -> List[dict]:
        """Fetch objects awaiting review."""
        objects = self.repo.get_pending_objects()
        return [_enrich_object_dict(obj) for obj in objects]

    def create_object(self, object_data: dict) -> dict:
        """Create a new artifact manually."""
        images_data = object_data.pop("images", [])
        for img in images_data:
            if isinstance(img, dict) and img.get("file_url"):
                img["file_url"] = ensure_stored_in_bucket(
                    img["file_url"],
                    object_identifier=object_data.get("inventory_number"),
                    prefix="obj"
                )
        try:
            obj = self.repo.add_object(object_data, images_data)
            app_logger.info("Created object", extra={"object_id": obj.id})
            return _enrich_object_dict(obj)
        except SQLAlchemyError as e:
            app_logger.error("Failed to create object", exc_info=True)
            raise BaseAppException("Internal database error during creation", 500)

    def update_object(self, object_id: int, object_data: dict) -> Optional[dict]:
        """Edit an artifact."""
        images_data = object_data.pop("images", [])
        for img in images_data:
            if isinstance(img, dict) and img.get("file_url"):
                img["file_url"] = ensure_stored_in_bucket(
                    img["file_url"],
                    object_identifier=object_id,
                    prefix="obj"
                )
        try:
            obj = self.repo.update_object(object_id, object_data, images_data)
            if not obj:
                app_logger.warning("Object not found for update", extra={"object_id": object_id})
                raise EntityNotFoundError("Object", object_id)
            app_logger.info("Updated object", extra={"object_id": object_id})
            return _enrich_object_dict(obj)
        except SQLAlchemyError as e:
            app_logger.error("Failed to update object", exc_info=True)
            raise BaseAppException("Internal database error during update", 500)

    def delete_object(self, object_id: int) -> bool:
        """Delete an artifact."""
        try:
            result = self.repo.delete_object(object_id)
            if not result:
                app_logger.warning("Object not found for deletion", extra={"object_id": object_id})
                raise EntityNotFoundError("Object", object_id)
            app_logger.info("Deleted object", extra={"object_id": object_id})
            return result
        except SQLAlchemyError as e:
            app_logger.error("Failed to delete object", exc_info=True)
            raise BaseAppException("Internal database error during deletion", 500)
