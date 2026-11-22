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
    Extracts unique citation texts from an object's source-linked images in deterministic image order.
    """
    citations = []
    seen = set()
    sorted_images = sorted(
        getattr(obj, "images", []) or [],
        key=lambda img: (
            getattr(img, "image_sequence", None) is None,
            getattr(img, "image_sequence", None) or 0,
            getattr(img, "id", None) or 0,
        ),
    )
    for img in sorted_images:
        if getattr(img, "source", None) and img.source.citation_text:
            text = img.source.citation_text.strip()
            if text and text not in seen:
                seen.add(text)
                citations.append(text)
    return citations


def extract_tags(obj: Object) -> List[str]:
    """Extracts unique tag names associated with an object's images, sorted alphabetically."""
    tags = set()
    for img in getattr(obj, "images", []):
        for t in getattr(img, "tags", []):
            if hasattr(t, "tag_name") and t.tag_name:
                tags.add(t.tag_name)
    return sorted(tags, key=lambda t: (t.lower(), t))


def build_assembled_caption(obj: Object) -> str:
    """
    Assembles a standard scholarly caption from 2_excel fields:
    [Description], [Object type], [Inscription], [Findspot], [Date],
    [Present Location], [Present Location Inventory Number].
    Returns custom `caption` override when present.
    """
    explicit = (getattr(obj, "caption", None) or "").strip()
    if explicit:
        return explicit

    parts: List[str] = []
    desc = (getattr(obj, "description", None) or "").strip()
    if desc and len(desc) <= 140:
        parts.append(desc)

    obj_type = (getattr(obj, "object_type", None) or "").strip()
    if obj_type:
        parts.append(obj_type)

    inscr_items = [
        (getattr(obj, "inscription_1", None) or "").strip(),
        (getattr(obj, "inscription_2", None) or "").strip(),
    ]
    inscr_items = [item for item in inscr_items if item]
    if inscr_items:
        parts.append(f"Inscribed: {' / '.join(inscr_items)}")
    elif getattr(obj, "inscription_present", None) is True:
        parts.append("Inscribed")

    findspot = (getattr(obj, "findspot", None) or "").strip()
    if findspot:
        parts.append(findspot)

    date_display = (getattr(obj, "date_display", None) or "").strip()
    if date_display and date_display.lower() != "unknown":
        parts.append(date_display)

    present_location = (getattr(obj, "present_location", None) or "").strip()
    if present_location:
        parts.append(present_location)

    inv = (getattr(obj, "inventory_number", None) or "").strip()
    if inv:
        if inv.lower().startswith(("inv", "bm", "ea", "wa")):
            parts.append(inv)
        else:
            parts.append(f"inv. {inv}")

    return ", ".join(parts)


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

    if "britishmuseum.org" in url_lower:
        if inventory_number:
            safe_inv = "".join(c if c.isalnum() else "_" for c in str(inventory_number))
            return f"/api/images/bm_{safe_inv}.jpg"
        match = re.search(r"/object/([^/]+)", url)
        if match:
            safe_inv = "".join(c if c.isalnum() else "_" for c in match.group(1))
            return f"/api/images/bm_{safe_inv}.jpg"
        return "/api/images/bm_default.jpg"

    return url


def _enrich_object_dict(obj: Object) -> dict:
    """Converts an ORM Object to a dict enriched with bibliography, caption, image metadata, and tags."""
    obj_dict = obj.__dict__.copy()
    obj_dict['bibliography'] = build_bibliography(obj)
    obj_dict['assembled_caption'] = build_assembled_caption(obj)

    inv_num = getattr(obj, "inventory_number", None)
    obj_id = getattr(obj, "id", None)
    sorted_images = sorted(
        getattr(obj, "images", []) or [],
        key=lambda img: (
            getattr(img, "image_sequence", None) is None,
            getattr(img, "image_sequence", None) or 0,
            getattr(img, "id", None) or 0,
        ),
    )

    for idx, img in enumerate(sorted_images, start=1):
        if isinstance(img, dict):
            seq = img.get("image_sequence") if img.get("image_sequence") is not None else idx
            raw_url = img.get("file_url") or ""
            img["file_url"] = _normalize_image_url(raw_url, inv_num) if raw_url else ""
            img["db_identifier"] = f"{obj_id}.{seq}" if obj_id is not None else str(seq)
        else:
            seq = img.image_sequence if getattr(img, "image_sequence", None) is not None else idx
            raw_url = getattr(img, "file_url", None) or ""
            source_obj = getattr(img, "source", None)
            img.file_url = _normalize_image_url(raw_url, inv_num) if raw_url else ""
            img.db_identifier = f"{obj_id}.{seq}" if obj_id is not None else str(seq)
            img.source_citation = source_obj.citation_text if source_obj else None

    obj_dict['images'] = sorted_images
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
        object_ids: Optional[List[int]] = None,
        tag_mode: str = "any",
        sort_by: str = "title",
        sort_order: str = "asc",
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
                object_ids=object_ids,
                tag_mode=tag_mode,
                sort_by=sort_by,
                sort_order=sort_order,
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
        images_data = object_data.pop("images", None)
        if images_data is not None:
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
