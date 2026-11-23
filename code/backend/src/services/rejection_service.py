"""
Persistent artifact rejection service and shared museum provenance helpers.
Tracks rejected museum & review-queue pieces so future discovery searches,
imports, and ingestion runs permanently skip them until explicitly unrejected.
"""
from __future__ import annotations

import re
from typing import Iterable, List, Optional, Tuple

from sqlalchemy import and_, func, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..logger import app_logger
from ..models import Object, RejectedArtifact

_MET_URL_RE = re.compile(r"metmuseum\.org/art/collection/search/(\d+)", re.IGNORECASE)
_MET_SRC_RE = re.compile(r"Met Object ID\s+(\d+)", re.IGNORECASE)
_VAM_URL_RE = re.compile(r"collections\.vam\.ac\.uk/item/([A-Za-z0-9_-]+)", re.IGNORECASE)
_VAM_SRC_RE = re.compile(r"V&A\s+([A-Za-z0-9_-]+)", re.IGNORECASE)
_AIC_URL_RE = re.compile(r"artic\.edu/artworks/(\d+)", re.IGNORECASE)
_CMA_URL_RE = re.compile(r"clevelandart\.org/art/([^/?#]+)", re.IGNORECASE)
_CMA_INV_RE = re.compile(r"^CMA-(\d+)$", re.IGNORECASE)
_BM_URL_RE = re.compile(r"britishmuseum\.org/collection/object/([^/?#]+)", re.IGNORECASE)
_BM_SRC_RE = re.compile(r"\bBM\s+(Q\d+)\b", re.IGNORECASE)
_BM_WIKIDATA_URL_RE = re.compile(r"wikidata\.org/wiki/(Q\d+)", re.IGNORECASE)


def normalize_key(val: Optional[str]) -> Optional[str]:
    """Normalize an identifier key for case-insensitive matching."""
    if not val or not isinstance(val, str):
        return None
    cleaned = val.strip().lower()
    return cleaned or None


def normalize_url(url: Optional[str]) -> Optional[str]:
    """Normalize an external URL by trimming whitespace and trailing slashes."""
    if not url or not isinstance(url, str):
        return None
    cleaned = url.strip().rstrip("/").lower()
    return cleaned or None


def extract_museum_provenance(
    *,
    external_url: Optional[str] = None,
    source_identifiers: Optional[Iterable[Optional[str]]] = None,
    present_location: Optional[str] = None,
    inventory_number: Optional[str] = None,
) -> Tuple[Optional[str], Optional[str]]:
    """Infer (museum_id, source_record_id) from stored object provenance fields."""
    url = (external_url or "").strip()
    inv = (inventory_number or "").strip()
    loc = (present_location or "").lower()

    if url:
        match = _MET_URL_RE.search(url)
        if match:
            return "met", match.group(1)
        match = _VAM_URL_RE.search(url)
        if match:
            return "vam", match.group(1)
        match = _AIC_URL_RE.search(url)
        if match:
            return "aic", match.group(1)
        match = _CMA_URL_RE.search(url)
        if match:
            cma_token = match.group(1)
            cma_match = _CMA_INV_RE.match(cma_token)
            if cma_match:
                return "cma", cma_match.group(1)
            inv_match = _CMA_INV_RE.match(inv)
            return "cma", (inv_match.group(1) if inv_match else None)
        match = _BM_URL_RE.search(url)
        if match:
            for raw_src in source_identifiers or ():
                if isinstance(raw_src, str):
                    src_match = _BM_SRC_RE.search(raw_src.strip())
                    if src_match:
                        return "bm", src_match.group(1).upper()
            return "bm", match.group(1)
        match = _BM_WIKIDATA_URL_RE.search(url)
        if match:
            return "bm", match.group(1).upper()

    for raw_src in source_identifiers or ():
        if not raw_src or not isinstance(raw_src, str):
            continue
        src = raw_src.strip()
        if not src:
            continue
        match = _MET_SRC_RE.search(src)
        if match:
            return "met", match.group(1)
        match = _VAM_SRC_RE.search(src)
        if match:
            return "vam", match.group(1)
        match = _BM_SRC_RE.search(src)
        if match:
            return "bm", match.group(1).upper()

    inv_match = _CMA_INV_RE.match(inv)
    if inv_match:
        return "cma", inv_match.group(1)

    if "metropolitan museum" in loc:
        return "met", None
    if "cleveland museum" in loc:
        return "cma", None
    if "art institute of chicago" in loc:
        return "aic", None
    if "victoria and albert" in loc:
        return "vam", None
    if "british museum" in loc:
        return "bm", None

    return None, None


def _clean_field(value: Optional[str], max_len: int, *, strip_trailing_slash: bool = False, lowercase: bool = False) -> Optional[str]:
    if not value or not isinstance(value, str):
        return None
    cleaned = value.strip()
    if strip_trailing_slash:
        cleaned = cleaned.rstrip("/")
    if not cleaned:
        return None
    if lowercase:
        cleaned = cleaned.lower()
    return cleaned[:max_len]


class RejectionService:
    """Manages persistent tombstones for rejected artifacts."""

    def __init__(self, db: Session):
        self.db = db

    def _find_matching_rows(
        self,
        *,
        museum_id: Optional[str] = None,
        source_record_id: Optional[str] = None,
        inventory_number: Optional[str] = None,
        external_url: Optional[str] = None,
        object_type: Optional[str] = None,
        present_location: Optional[str] = None,
        date_display: Optional[str] = None,
    ) -> List[RejectedArtifact]:
        norm_mid = normalize_key(museum_id)
        norm_sid = normalize_key(source_record_id)
        norm_inv = normalize_key(inventory_number)
        norm_url = normalize_url(external_url)

        predicates = []
        if norm_mid and norm_sid:
            predicates.append(
                and_(
                    func.lower(func.trim(RejectedArtifact.museum_id)) == norm_mid,
                    func.lower(func.trim(RejectedArtifact.source_record_id)) == norm_sid,
                )
            )
        if norm_inv:
            predicates.append(func.lower(func.trim(RejectedArtifact.inventory_number)) == norm_inv)
        if norm_url:
            predicates.append(
                func.lower(func.trim(RejectedArtifact.external_url)).in_([norm_url, f"{norm_url}/"])
            )

        if not predicates:
            norm_type = normalize_key(object_type)
            if not norm_type:
                return []
            norm_loc = normalize_key(present_location) or ""
            norm_date = normalize_key(date_display) or ""
            predicates.append(
                and_(
                    func.lower(func.trim(func.coalesce(RejectedArtifact.object_type, ""))) == norm_type,
                    func.lower(func.trim(func.coalesce(RejectedArtifact.present_location, ""))) == norm_loc,
                    func.lower(func.trim(func.coalesce(RejectedArtifact.date_display, ""))) == norm_date,
                )
            )

        return (
            self.db.query(RejectedArtifact)
            .filter(or_(*predicates))
            .order_by(RejectedArtifact.id.asc())
            .all()
        )

    def is_rejected(
        self,
        *,
        museum_id: Optional[str] = None,
        source_record_id: Optional[str] = None,
        inventory_number: Optional[str] = None,
        external_url: Optional[str] = None,
        object_type: Optional[str] = None,
        present_location: Optional[str] = None,
        date_display: Optional[str] = None,
    ) -> bool:
        """Return True if any persisted rejection matches the given artifact identifiers."""
        return bool(
            self._find_matching_rows(
                museum_id=museum_id,
                source_record_id=source_record_id,
                inventory_number=inventory_number,
                external_url=external_url,
                object_type=object_type,
                present_location=present_location,
                date_display=date_display,
            )
        )

    def record_rejection(
        self,
        *,
        museum_id: Optional[str] = None,
        source_record_id: Optional[str] = None,
        inventory_number: Optional[str] = None,
        external_url: Optional[str] = None,
        object_type: Optional[str] = None,
        present_location: Optional[str] = None,
        date_display: Optional[str] = None,
        commit: bool = False,
    ) -> Tuple[Optional[RejectedArtifact], bool]:
        """Idempotently record a rejected artifact tombstone."""
        clean_mid = _clean_field(museum_id, 32, lowercase=True)
        clean_sid = _clean_field(source_record_id, 100)
        clean_inv = _clean_field(inventory_number, 100)
        clean_url = _clean_field(external_url, 500, strip_trailing_slash=True)
        clean_type = _clean_field(object_type, 255)
        clean_loc = _clean_field(present_location, 255)
        clean_date = _clean_field(date_display, 255)

        if not (clean_mid and clean_sid) and not clean_inv and not clean_url and not clean_type:
            return None, False

        try:
            matches = self._find_matching_rows(
                museum_id=clean_mid,
                source_record_id=clean_sid,
                inventory_number=clean_inv,
                external_url=clean_url,
                object_type=clean_type,
                present_location=clean_loc,
                date_display=clean_date,
            )
            if matches:
                existing = matches[0]
                updates = {
                    "museum_id": clean_mid,
                    "source_record_id": clean_sid,
                    "inventory_number": clean_inv,
                    "external_url": clean_url,
                    "object_type": clean_type,
                    "present_location": clean_loc,
                    "date_display": clean_date,
                }
                for field, value in updates.items():
                    current = getattr(existing, field)
                    if value and (current is None or not str(current).strip()):
                        setattr(existing, field, value)
                self.db.flush()
                if commit:
                    self.db.commit()
                    self.db.refresh(existing)
                return existing, False

            row = RejectedArtifact(
                museum_id=clean_mid,
                source_record_id=clean_sid,
                inventory_number=clean_inv,
                external_url=clean_url,
                object_type=clean_type,
                present_location=clean_loc,
                date_display=clean_date,
            )
            self.db.add(row)
            self.db.flush()
            if commit:
                self.db.commit()
                self.db.refresh(row)
            return row, True
        except SQLAlchemyError:
            app_logger.error("Failed persisting rejected artifact record", exc_info=True)
            if commit:
                self.db.rollback()
            raise

    def record_rejected_object(
        self,
        obj: Object,
        *,
        commit: bool = False,
    ) -> Tuple[Optional[RejectedArtifact], bool]:
        """Extract museum provenance from an ORM Object and persist a rejection tombstone."""
        source_identifiers = [
            getattr(img, "source_identifier", None)
            for img in (getattr(obj, "images", None) or [])
        ]
        museum_id, source_record_id = extract_museum_provenance(
            external_url=getattr(obj, "external_url", None),
            source_identifiers=source_identifiers,
            present_location=getattr(obj, "present_location", None),
            inventory_number=getattr(obj, "inventory_number", None),
        )
        return self.record_rejection(
            museum_id=museum_id,
            source_record_id=source_record_id,
            inventory_number=getattr(obj, "inventory_number", None),
            external_url=getattr(obj, "external_url", None),
            object_type=getattr(obj, "object_type", None),
            present_location=getattr(obj, "present_location", None),
            date_display=getattr(obj, "date_display", None),
            commit=commit,
        )

    def remove_rejection_for_object(self, obj: Object, *, commit: bool = False) -> int:
        """Delete rejection tombstones associated with an Object restored from rejected status."""
        source_identifiers = [
            getattr(img, "source_identifier", None)
            for img in (getattr(obj, "images", None) or [])
        ]
        museum_id, source_record_id = extract_museum_provenance(
            external_url=getattr(obj, "external_url", None),
            source_identifiers=source_identifiers,
            present_location=getattr(obj, "present_location", None),
            inventory_number=getattr(obj, "inventory_number", None),
        )
        try:
            matches = self._find_matching_rows(
                museum_id=museum_id,
                source_record_id=source_record_id,
                inventory_number=getattr(obj, "inventory_number", None),
                external_url=getattr(obj, "external_url", None),
                object_type=getattr(obj, "object_type", None),
                present_location=getattr(obj, "present_location", None),
                date_display=getattr(obj, "date_display", None),
            )
            for row in matches:
                self.db.delete(row)
            self.db.flush()
            if commit:
                self.db.commit()
            return len(matches)
        except SQLAlchemyError:
            app_logger.error("Failed removing rejected artifact record", exc_info=True)
            if commit:
                self.db.rollback()
            raise

    def delete_by_id(self, rejected_id: int) -> bool:
        """Delete a rejection tombstone by primary key."""
        if rejected_id is None:
            return False
        row = self.db.query(RejectedArtifact).filter(RejectedArtifact.id == rejected_id).first()
        if not row:
            return False
        try:
            self.db.delete(row)
            self.db.commit()
            return True
        except SQLAlchemyError:
            app_logger.error("Failed deleting rejected artifact %s", rejected_id, exc_info=True)
            self.db.rollback()
            raise
