"""
Admin-triggered open-access museum discovery and import service.
Queries predefined public museum APIs with editable keywords & date ranges,
populates full 2_excel scholarly metadata, prevents duplicates, and stages
imported records in the pending Review Queue.
"""
from __future__ import annotations

import re
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import config
from ..exceptions import ValidationError
from ..logger import app_logger
from ..models import DiscoveryKeyword, Image, Object, Source, Tag
from ..schemas import (
    DiscoveryCandidate,
    DiscoverySearchRequest,
    MuseumKey,
)
from ..url_validator import ALLOWED_API_DOMAINS, is_safe_image_url, validate_url
from .object_service import build_assembled_caption
from .s3_service import download_and_store_image

MAX_SAVED_KEYWORDS = 200
USER_AGENT = "AcademicArtifactDB/1.0 (Research Project)"
DEFAULT_KEYWORDS: List[str] = [
    "craftsman",
    "glass",
    "potter",
    "workshop",
    "weaver",
    "blacksmith",
    "scribe",
    "sculptor",
]
DEFAULT_DATE_START = 0
DEFAULT_DATE_END = 899
DEFAULT_LIMIT_PER_MUSEUM = 10

PREDEFINED_MUSEUMS: List[Dict[str, Any]] = [
    {
        "id": "met",
        "name": "The Metropolitan Museum of Art",
        "present_location": "The Metropolitan Museum of Art, New York",
        "description": "Met Collection Open Access API v1.1 (CC0 public domain antiquities and medieval art).",
        "default_keywords": list(DEFAULT_KEYWORDS),
        "default_date_start": DEFAULT_DATE_START,
        "default_date_end": DEFAULT_DATE_END,
        "default_limit": DEFAULT_LIMIT_PER_MUSEUM,
    },
    {
        "id": "cma",
        "name": "Cleveland Museum of Art",
        "present_location": "The Cleveland Museum of Art, Cleveland",
        "description": "CMA Open Access API (CC0 artworks with measurements, provenance, and inscriptions).",
        "default_keywords": list(DEFAULT_KEYWORDS),
        "default_date_start": DEFAULT_DATE_START,
        "default_date_end": DEFAULT_DATE_END,
        "default_limit": DEFAULT_LIMIT_PER_MUSEUM,
    },
    {
        "id": "aic",
        "name": "Art Institute of Chicago",
        "present_location": "The Art Institute of Chicago, Chicago",
        "description": "AIC Public Collection API v1 + IIIF Image Service (public domain works).",
        "default_keywords": list(DEFAULT_KEYWORDS),
        "default_date_start": DEFAULT_DATE_START,
        "default_date_end": DEFAULT_DATE_END,
        "default_limit": DEFAULT_LIMIT_PER_MUSEUM,
    },
    {
        "id": "vam",
        "name": "Victoria and Albert Museum",
        "present_location": "Victoria and Albert Museum, London",
        "description": "V&A Collection API v2 + Framemark IIIF Image Service.",
        "default_keywords": list(DEFAULT_KEYWORDS),
        "default_date_start": DEFAULT_DATE_START,
        "default_date_end": DEFAULT_DATE_END,
        "default_limit": DEFAULT_LIMIT_PER_MUSEUM,
    },
]

# Ordered from specific sites to broad regions for deterministic coordinate inference
COORDINATE_RULES: List[Tuple[Tuple[str, ...], Tuple[float, float]]] = [
    (("thebes", "karnak", "luxor", "sennedjem", "deir el-medina", "nebamun"), (25.7333, 32.6000)),
    (("beni hasan",), (27.9296, 30.8753)),
    (("alexandria",), (31.2001, 29.9187)),
    (("cairo", "fustat", "giza"), (30.0444, 31.2357)),
    (("vulci",), (42.4184, 11.6317)),
    (("pompeii", "herculaneum", "naples", "campania"), (40.7462, 14.4989)),
    (("frascati", "tusculum"), (41.8075, 12.6808)),
    (("ravenna",), (44.4184, 12.2035)),
    (("aquileia",), (45.7697, 13.3700)),
    (("rome", "roman empire", "roman"), (41.9028, 12.4964)),
    (("italy", "etruria", "etruscan"), (42.5000, 12.5000)),
    (("athens", "attica"), (37.9838, 23.7275)),
    (("corinth",), (37.9060, 22.8805)),
    (("boeotia",), (38.3667, 23.1833)),
    (("greece", "greek", "byzantine"), (38.0000, 23.7000)),
    (("constantinople", "istanbul", "byzantium"), (41.0082, 28.9784)),
    (("ephesus",), (37.9390, 27.3410)),
    (("anatolia", "turkey", "asia minor"), (39.0000, 35.0000)),
    (("cyprus", "marion-arsinoe", "cypriot"), (35.0361, 32.4264)),
    (("antioch", "palmyra", "syria", "dura-europos", "damascus"), (34.8021, 38.9968)),
    (("jerusalem", "levant", "palestine", "israel", "jordan", "lebanon"), (31.7683, 35.2137)),
    (("nineveh",), (36.3594, 43.1528)),
    (("babylon", "uruk", "mesopotamia", "iraq"), (31.3260, 45.6360)),
    (("iran", "persia", "sasanian", "sassanian"), (32.4279, 53.6880)),
    (("carthage", "tunisia"), (36.8528, 10.3233)),
    (("north africa",), (34.0000, 9.0000)),
    (("egypt", "coptic"), (26.8206, 30.8025)),
    (("vindolanda",), (54.9912, -2.3607)),
    (("london", "britain", "england", "united kingdom", "anglo-saxon"), (51.5072, -0.1276)),
    (("france", "gaul", "frankish", "merovingian", "carolingian", "paris", "lyon"), (46.2276, 2.2137)),
    (("spain", "hispania", "visigothic"), (40.4637, -3.7492)),
    (("germany", "germania", "cologne", "trier", "rhineland"), (50.9375, 6.9603)),
    (("china", "tang", "han", "sui"), (34.3416, 108.9398)),
    (("india", "gupta", "kushan"), (25.3176, 82.9739)),
    (("japan", "nara", "asuka"), (34.6851, 135.8048)),
    (("peru", "moche", "nazca"), (-8.1116, -79.0288)),
    (("mexico", "maya", "teotihuacan"), (19.6925, -98.8438)),
]

FILLED_FIELD_KEYS = (
    "object_type",
    "material",
    "findspot",
    "production_location",
    "present_location",
    "inventory_number",
    "description",
    "date_display",
    "date_basis",
    "width",
    "height",
    "depth",
    "dimensions_display",
    "weight",
    "completeness",
    "inscription_present",
    "inscription_1",
    "inscription_2",
    "object_group",
    "publications",
    "external_url",
    "images",
    "tags",
)


def strip_html(raw: Optional[str]) -> Optional[str]:
    """Strip HTML tags and collapse redundant whitespace."""
    if not raw or not isinstance(raw, str):
        return None
    text = BeautifulSoup(raw, "html.parser").get_text(" ", strip=True)
    cleaned = re.sub(r"\s+", " ", text).strip()
    return cleaned or None


def _clean_text(value: Any, max_len: Optional[int] = None) -> Optional[str]:
    if value is None:
        return None
    text = re.sub(r"\s+", " ", str(value)).strip()
    if not text:
        return None
    if max_len is not None and len(text) > max_len:
        return text[:max_len].rstrip()
    return text


def infer_coordinates(
    findspot: Optional[str],
    production_location: Optional[str] = None,
) -> Tuple[Optional[float], Optional[float]]:
    """Infer representative map coordinates from findspot or production location text."""
    for candidate_text in (findspot, production_location):
        if not candidate_text or not isinstance(candidate_text, str):
            continue
        lowered = candidate_text.lower()
        for tokens, coords in COORDINATE_RULES:
            if any(tok in lowered for tok in tokens):
                return coords
    return None, None


def infer_completeness(*texts: Optional[str]) -> Optional[str]:
    """Detect whether scholarly titles or descriptions indicate a fragment."""
    combined = " ".join(t.lower() for t in texts if isinstance(t, str) and t.strip())
    if "fragment" in combined:
        return "Fragmentary"
    return None


def count_filled_fields(candidate: Dict[str, Any]) -> int:
    """Count how many 2_excel fields are populated on a discovered artifact."""
    filled = 0
    for key in FILLED_FIELD_KEYS:
        val = candidate.get(key)
        if val is None or val == "" or val == []:
            continue
        filled += 1
    return filled


def _norm_key(val: Optional[str]) -> Optional[str]:
    if not val or not isinstance(val, str):
        return None
    cleaned = val.strip().lower()
    return cleaned or None


def _norm_url(url: Optional[str]) -> Optional[str]:
    if not url or not isinstance(url, str):
        return None
    cleaned = url.strip().rstrip("/").lower()
    return cleaned or None


def _sanitize_https_url(url: Optional[str]) -> Optional[str]:
    cleaned = _clean_text(url, max_len=500)
    if not cleaned:
        return None
    parsed = urlparse(cleaned)
    if parsed.scheme.lower() != "https" or not parsed.netloc:
        return None
    return cleaned


def _dedupe_tags(raw_tags: List[Optional[str]], max_tags: int = 12) -> List[str]:
    seen: Set[str] = set()
    cleaned: List[str] = []
    for raw in raw_tags:
        tag = _clean_text(raw, max_len=100)
        if not tag:
            continue
        low = tag.lower()
        if low not in seen:
            seen.add(low)
            cleaned.append(tag)
    return sorted(cleaned[:max_tags], key=lambda t: (t.lower(), t))


def _finalize_candidate(candidate: Dict[str, Any]) -> Dict[str, Any]:
    """Attach inferred coordinates, assembled caption, and filled field count."""
    if candidate.get("latitude") is None or candidate.get("longitude") is None:
        lat, lon = infer_coordinates(candidate.get("findspot"), candidate.get("production_location"))
        candidate["latitude"] = lat
        candidate["longitude"] = lon

    candidate["external_url"] = _sanitize_https_url(candidate.get("external_url"))
    candidate["tags"] = _dedupe_tags(candidate.get("tags") or [])
    candidate["assembled_caption"] = build_assembled_caption(SimpleNamespace(**candidate))
    candidate["filled_fields_count"] = count_filled_fields(candidate)
    return candidate


class ExistingArtifactIndex:
    """In-memory index of existing database artifacts to guarantee zero duplicates."""

    def __init__(self, db: Session):
        self.inventory_numbers: Set[str] = set()
        self.external_urls: Set[str] = set()
        self.fallback_signatures: Set[Tuple[str, str, str]] = set()

        rows = db.query(
            Object.inventory_number,
            Object.external_url,
            Object.object_type,
            Object.present_location,
            Object.date_display,
        ).all()

        for inv, ext_url, obj_type, pres_loc, date_disp in rows:
            self.register(
                inventory_number=inv,
                external_url=ext_url,
                object_type=obj_type,
                present_location=pres_loc,
                date_display=date_disp,
            )

    def contains(
        self,
        *,
        inventory_number: Optional[str] = None,
        source_record_id: Optional[str] = None,
        external_url: Optional[str] = None,
        object_type: Optional[str] = None,
        present_location: Optional[str] = None,
        date_display: Optional[str] = None,
    ) -> bool:
        norm_inv = _norm_key(inventory_number)
        if norm_inv and norm_inv in self.inventory_numbers:
            return True

        norm_src = _norm_key(source_record_id)
        if norm_src and norm_src in self.inventory_numbers:
            return True

        norm_ext = _norm_url(external_url)
        if norm_ext and norm_ext in self.external_urls:
            return True

        if not norm_inv and object_type:
            sig = (
                object_type.strip().lower(),
                (present_location or "").strip().lower(),
                (date_display or "").strip().lower(),
            )
            if sig in self.fallback_signatures:
                return True
        return False

    def register(
        self,
        *,
        inventory_number: Optional[str] = None,
        source_record_id: Optional[str] = None,
        external_url: Optional[str] = None,
        object_type: Optional[str] = None,
        present_location: Optional[str] = None,
        date_display: Optional[str] = None,
    ) -> None:
        norm_inv = _norm_key(inventory_number)
        if norm_inv:
            self.inventory_numbers.add(norm_inv)

        norm_src = _norm_key(source_record_id)
        if norm_src:
            self.inventory_numbers.add(norm_src)

        norm_ext = _norm_url(external_url)
        if norm_ext:
            self.external_urls.add(norm_ext)

        if object_type:
            self.fallback_signatures.add((
                object_type.strip().lower(),
                (present_location or "").strip().lower(),
                (date_display or "").strip().lower(),
            ))


def _request_json(
    method: str,
    url: str,
    *,
    params: Optional[Dict[str, Any]] = None,
    json_body: Optional[Dict[str, Any]] = None,
    timeout: int = 10,
    allow_404: bool = False,
) -> Optional[Dict[str, Any]]:
    """Perform an SSRF-validated outbound API request returning parsed JSON."""
    validate_url(url, ALLOWED_API_DOMAINS)
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }
    if method == "POST":
        resp = requests.post(url, json=json_body, headers=headers, timeout=timeout)
    else:
        resp = requests.get(url, params=params, headers=headers, timeout=timeout)

    if allow_404 and resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()


def _dates_overlap(
    item_start: Optional[int],
    item_end: Optional[int],
    filter_start: int,
    filter_end: int,
) -> bool:
    if item_start is None and item_end is None:
        return False
    start = item_start if item_start is not None else item_end
    end = item_end if item_end is not None else item_start
    if start > end:
        start, end = end, start
    return end >= filter_start and start <= filter_end


def _coerce_int(value: Any) -> Optional[int]:
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        match = re.search(r"-?\d+", str(value))
        return int(match.group(0)) if match else None


def _coerce_float(value: Any, digits: int = 2) -> Optional[float]:
    if value is None or isinstance(value, bool):
        return None
    try:
        return round(float(value), digits)
    except (ValueError, TypeError):
        return None


class MetMuseumAdapter:
    """Adapter for The Metropolitan Museum of Art Collection API v1.1."""

    museum_id: MuseumKey = "met"
    museum_name = "The Metropolitan Museum of Art"
    present_location = "The Metropolitan Museum of Art, New York"
    search_url = "https://collectionapi.metmuseum.org/public/collection/v1.1/search"
    object_url = "https://collectionapi.metmuseum.org/public/collection/v1/objects"

    def discover(
        self,
        keywords: List[str],
        date_start: int,
        date_end: int,
        limit: int,
        index: ExistingArtifactIndex,
    ) -> Tuple[List[Dict[str, Any]], int, int]:
        candidates: List[Dict[str, Any]] = []
        fetched_count = 0
        duplicates_skipped = 0

        queued_ids: List[Tuple[int, str]] = []
        seen_oids: Set[int] = set()
        detail_cap = min(limit * 4, 40)

        for kw in keywords:
            if len(queued_ids) >= detail_cap:
                break
            data = _request_json(
                "GET",
                self.search_url,
                params={
                    "hasImages": "true",
                    "q": kw,
                    "dateBegin": date_start,
                    "dateEnd": date_end,
                    "limit": min(limit * 3, 50),
                    "offset": 0,
                },
                timeout=10,
            ) or {}
            for oid in data.get("objectIDs") or []:
                if oid in seen_oids:
                    continue
                seen_oids.add(oid)
                if index.contains(source_record_id=str(oid)):
                    fetched_count += 1
                    duplicates_skipped += 1
                    continue
                queued_ids.append((oid, kw))
                if len(queued_ids) >= detail_cap:
                    break

        for oid, matched_kw in queued_ids:
            if len(candidates) >= limit:
                break
            obj_data = _request_json(
                "GET",
                f"{self.object_url}/{oid}",
                timeout=8,
                allow_404=True,
            )
            if not obj_data:
                continue
            fetched_count += 1

            if obj_data.get("isPublicDomain") is False:
                continue

            item_start = _coerce_int(obj_data.get("objectBeginDate"))
            item_end = _coerce_int(obj_data.get("objectEndDate"))
            if not _dates_overlap(item_start, item_end, date_start, date_end):
                continue

            inv = _clean_text(obj_data.get("accessionNumber"), max_len=100) or str(oid)
            ext_url = _sanitize_https_url(obj_data.get("objectURL"))
            title = _clean_text(obj_data.get("title")) or _clean_text(obj_data.get("objectName")) or "Untitled Artifact"
            date_disp = _clean_text(obj_data.get("objectDate"), max_len=255) or f"{item_start}–{item_end}"

            if index.contains(
                inventory_number=inv,
                source_record_id=str(oid),
                external_url=ext_url,
                object_type=title,
                present_location=self.present_location,
                date_display=date_disp,
            ):
                duplicates_skipped += 1
                continue

            parsed = self._parse_record(obj_data, oid, inv, title, date_disp, item_start, item_end, matched_kw, ext_url)
            if not parsed["images"]:
                continue

            index.register(
                inventory_number=parsed.get("inventory_number"),
                source_record_id=str(oid),
                external_url=parsed.get("external_url"),
                object_type=parsed.get("object_type"),
                present_location=parsed.get("present_location"),
                date_display=parsed.get("date_display"),
            )
            candidates.append(parsed)

        return candidates, fetched_count, duplicates_skipped

    def _parse_record(
        self,
        obj_data: Dict[str, Any],
        oid: int,
        inv: str,
        title: str,
        date_disp: str,
        item_start: Optional[int],
        item_end: Optional[int],
        matched_kw: str,
        ext_url: Optional[str],
    ) -> Dict[str, Any]:
        medium = _clean_text(obj_data.get("medium"), max_len=255)
        findspot_parts = [
            _clean_text(obj_data.get(k))
            for k in ("excavation", "locale", "city", "region", "country")
        ]
        findspot = ", ".join(dict.fromkeys(p for p in findspot_parts if p)) or None
        culture = _clean_text(obj_data.get("culture"), max_len=255)
        period = _clean_text(obj_data.get("period"))
        dynasty = _clean_text(obj_data.get("dynasty"))
        reign = _clean_text(obj_data.get("reign"))
        date_basis = "; ".join(p for p in (period, dynasty, reign, culture) if p) or None

        height = width = depth = None
        weight = None
        for m in obj_data.get("measurements") or []:
            elems = m.get("elementMeasurements") or {}
            if height is None:
                height = _coerce_float(elems.get("Height"))
            if width is None:
                width = _coerce_float(elems.get("Width") or elems.get("Diameter"))
            if depth is None:
                depth = _coerce_float(elems.get("Depth") or elems.get("Thickness") or elems.get("Length"))
            if weight is None and elems.get("Weight") is not None:
                w_val = _coerce_float(elems.get("Weight"))
                if w_val is not None:
                    weight = f"{round(w_val, 2):g} kg"

        classification = _clean_text(obj_data.get("classification"))
        credit = _clean_text(obj_data.get("creditLine"))
        desc_parts = [
            p for p in (
                classification,
                f"Medium: {medium}" if medium else None,
                f"Culture: {culture}" if culture else None,
                f"Period: {period}" if period else None,
                credit,
            ) if p
        ]
        description = ". ".join(desc_parts) if desc_parts else None

        artist = _clean_text(obj_data.get("artistDisplayName"))
        citation = (
            f"{artist + '. ' if artist else ''}{title}. {date_disp}. "
            f"{medium or 'Unknown medium'}. {self.present_location}. {ext_url or ''}"
        ).strip()

        raw_imgs: List[Tuple[str, str, str]] = []
        primary = obj_data.get("primaryImage") or obj_data.get("primaryImageSmall")
        if primary and is_safe_image_url(primary):
            raw_imgs.append((primary, "Colour photo", "Front"))
        for idx, add_url in enumerate(obj_data.get("additionalImages") or [], start=2):
            if len(raw_imgs) >= 3:
                break
            if add_url and is_safe_image_url(add_url):
                raw_imgs.append((add_url, "Colour photo", f"View {idx}"))

        images = [
            {
                "file_url": url,
                "image_type": img_type,
                "view_type": view_type,
                "image_sequence": seq,
                "source_identifier": f"Met Object ID {oid}" if seq == 1 else f"Met Object ID {oid} (alt {seq})",
                "source_citation": citation,
            }
            for seq, (url, img_type, view_type) in enumerate(raw_imgs, start=1)
        ]

        tags = [t.get("term") for t in (obj_data.get("tags") or []) if isinstance(t, dict)]
        tags.extend([culture, period, matched_kw])

        return _finalize_candidate({
            "museum_id": self.museum_id,
            "museum_name": self.museum_name,
            "source_record_id": str(oid),
            "matched_keyword": matched_kw,
            "object_type": title[:255],
            "material": medium,
            "findspot": _clean_text(findspot, max_len=255),
            "production_location": culture,
            "present_location": _clean_text(obj_data.get("repository"), max_len=255) or self.present_location,
            "inventory_number": inv,
            "description": description,
            "date_display": date_disp,
            "date_start": item_start if item_start is not None else item_end or 0,
            "date_end": item_end if item_end is not None else item_start or 0,
            "date_basis": date_basis,
            "width": width,
            "height": height,
            "depth": depth,
            "unit": "cm",
            "dimensions_display": _clean_text(obj_data.get("dimensions"), max_len=255),
            "weight": weight,
            "completeness": infer_completeness(title, obj_data.get("objectName"), description),
            "inscription_present": None,
            "inscription_1": None,
            "inscription_2": None,
            "object_group": _clean_text(obj_data.get("department"), max_len=255),
            "publications": None,
            "external_url": ext_url,
            "tags": tags,
            "images": images,
        })


class ClevelandMuseumAdapter:
    """Adapter for The Cleveland Museum of Art Open Access API."""

    museum_id: MuseumKey = "cma"
    museum_name = "Cleveland Museum of Art"
    present_location = "The Cleveland Museum of Art, Cleveland"
    search_url = "https://openaccess-api.clevelandart.org/api/artworks/"

    def discover(
        self,
        keywords: List[str],
        date_start: int,
        date_end: int,
        limit: int,
        index: ExistingArtifactIndex,
    ) -> Tuple[List[Dict[str, Any]], int, int]:
        candidates: List[Dict[str, Any]] = []
        fetched_count = 0
        duplicates_skipped = 0

        for kw in keywords:
            if len(candidates) >= limit:
                break
            data = _request_json(
                "GET",
                self.search_url,
                params={
                    "q": kw,
                    "created_after": date_start,
                    "created_before": date_end,
                    "has_image": 1,
                    "cc0": 1,
                    "limit": min(limit * 2, 25),
                },
                timeout=10,
            ) or {}
            for item in data.get("data") or []:
                if len(candidates) >= limit:
                    break
                fetched_count += 1
                item_start = _coerce_int(item.get("creation_date_earliest"))
                item_end = _coerce_int(item.get("creation_date_latest"))
                if not _dates_overlap(item_start, item_end, date_start, date_end):
                    continue

                rec_id = str(item.get("id") or "")
                inv = _clean_text(item.get("accession_number"), max_len=100) or (f"CMA-{rec_id}" if rec_id else None)
                ext_url = _sanitize_https_url(item.get("url"))
                title = _clean_text(item.get("title")) or _clean_text(item.get("type")) or "Untitled Artifact"
                date_disp = _clean_text(item.get("creation_date") or item.get("date_text"), max_len=255) or f"{item_start}–{item_end}"

                if index.contains(
                    inventory_number=inv,
                    source_record_id=rec_id,
                    external_url=ext_url,
                    object_type=title,
                    present_location=self.present_location,
                    date_display=date_disp,
                ):
                    duplicates_skipped += 1
                    continue

                parsed = self._parse_record(item, rec_id, inv, title, date_disp, item_start, item_end, kw, ext_url)
                if not parsed["images"]:
                    continue

                index.register(
                    inventory_number=parsed.get("inventory_number"),
                    source_record_id=rec_id,
                    external_url=parsed.get("external_url"),
                    object_type=parsed.get("object_type"),
                    present_location=parsed.get("present_location"),
                    date_display=parsed.get("date_display"),
                )
                candidates.append(parsed)

        return candidates, fetched_count, duplicates_skipped

    def _parse_record(
        self,
        item: Dict[str, Any],
        rec_id: str,
        inv: Optional[str],
        title: str,
        date_disp: str,
        item_start: Optional[int],
        item_end: Optional[int],
        matched_kw: str,
        ext_url: Optional[str],
    ) -> Dict[str, Any]:
        culture_list = [c for c in (item.get("culture") or []) if isinstance(c, str) and c.strip()]
        culture_str = ", ".join(culture_list) or None

        # CMA stores dimensions in meters inside nested dicts
        height = width = depth = None
        dims_obj = item.get("dimensions")
        if isinstance(dims_obj, dict):
            for section in dims_obj.values():
                if not isinstance(section, dict):
                    continue
                if height is None and section.get("height") is not None:
                    val = _coerce_float(section.get("height"), digits=6)
                    height = round(val * 100, 2) if val is not None else None
                if width is None and section.get("width") is not None:
                    val = _coerce_float(section.get("width"), digits=6)
                    width = round(val * 100, 2) if val is not None else None
                if depth is None and section.get("depth") is not None:
                    val = _coerce_float(section.get("depth"), digits=6)
                    depth = round(val * 100, 2) if val is not None else None

        inscr_list = [
            _clean_text(i.get("inscription") if isinstance(i, dict) else i)
            for i in (item.get("inscriptions") or [])
        ]
        inscr_list = [i for i in inscr_list if i]
        inscription_present = True if inscr_list else None

        cit_list = [
            _clean_text(c.get("citation") if isinstance(c, dict) else c)
            for c in (item.get("citations") or [])
        ]
        publications = "; ".join(c for c in cit_list if c) or None

        description = (
            strip_html(item.get("description"))
            or strip_html(item.get("wall_description"))
            or strip_html(item.get("did_you_know"))
            or _clean_text(item.get("tombstone"))
        )

        citation = (
            f"The Cleveland Museum of Art. \"{title}.\" {date_disp}. "
            f"{_clean_text(item.get('technique')) or 'Unknown medium'}. {ext_url or ''}"
        ).strip()

        raw_imgs: List[Tuple[str, str, str]] = []
        web_url = ((item.get("images") or {}).get("web") or {}).get("url")
        if web_url and is_safe_image_url(web_url):
            raw_imgs.append((web_url, "Colour photo", "Front"))
        for idx, alt in enumerate(item.get("alternate_images") or [], start=2):
            if len(raw_imgs) >= 3:
                break
            alt_url = (alt.get("web") or {}).get("url") if isinstance(alt, dict) else None
            if alt_url and is_safe_image_url(alt_url):
                raw_imgs.append((alt_url, "Colour photo", f"View {idx}"))

        images = [
            {
                "file_url": url,
                "image_type": img_type,
                "view_type": view_type,
                "image_sequence": seq,
                "source_identifier": f"CMA {inv or rec_id}" if seq == 1 else f"CMA {inv or rec_id} (alt {seq})",
                "source_citation": citation,
            }
            for seq, (url, img_type, view_type) in enumerate(raw_imgs, start=1)
        ]

        tags = list(culture_list) + [item.get("type"), item.get("department"), matched_kw]

        return _finalize_candidate({
            "museum_id": self.museum_id,
            "museum_name": self.museum_name,
            "source_record_id": rec_id,
            "matched_keyword": matched_kw,
            "object_type": title[:255],
            "material": _clean_text(item.get("technique"), max_len=255),
            "findspot": _clean_text(item.get("find_spot"), max_len=255),
            "production_location": _clean_text(culture_str, max_len=255),
            "present_location": self.present_location,
            "inventory_number": inv,
            "description": description,
            "date_display": date_disp,
            "date_start": item_start if item_start is not None else item_end or 0,
            "date_end": item_end if item_end is not None else item_start or 0,
            "date_basis": _clean_text(culture_str),
            "width": width,
            "height": height,
            "depth": depth,
            "unit": "cm",
            "dimensions_display": _clean_text(item.get("measurements"), max_len=255),
            "weight": None,
            "completeness": infer_completeness(title, description),
            "inscription_present": inscription_present,
            "inscription_1": inscr_list[0] if len(inscr_list) > 0 else None,
            "inscription_2": inscr_list[1] if len(inscr_list) > 1 else None,
            "object_group": _clean_text(item.get("collection") or item.get("department"), max_len=255),
            "publications": publications,
            "external_url": ext_url,
            "tags": tags,
            "images": images,
        })


class ArtInstituteChicagoAdapter:
    """Adapter for The Art Institute of Chicago Public Collection API v1."""

    museum_id: MuseumKey = "aic"
    museum_name = "Art Institute of Chicago"
    present_location = "The Art Institute of Chicago, Chicago"
    search_url = "https://api.artic.edu/api/v1/artworks/search"
    fields = [
        "id",
        "title",
        "artwork_type_title",
        "medium_display",
        "dimensions",
        "dimensions_detail",
        "date_display",
        "date_start",
        "date_end",
        "place_of_origin",
        "main_reference_number",
        "description",
        "short_description",
        "inscriptions",
        "publication_history",
        "provenance_text",
        "credit_line",
        "image_id",
        "alt_image_ids",
        "term_titles",
        "style_title",
        "is_public_domain",
    ]

    def discover(
        self,
        keywords: List[str],
        date_start: int,
        date_end: int,
        limit: int,
        index: ExistingArtifactIndex,
    ) -> Tuple[List[Dict[str, Any]], int, int]:
        candidates: List[Dict[str, Any]] = []
        fetched_count = 0
        duplicates_skipped = 0

        for kw in keywords:
            if len(candidates) >= limit:
                break
            body = {
                "q": kw,
                "query": {
                    "bool": {
                        "filter": [
                            {"range": {"date_start": {"lte": date_end}}},
                            {"range": {"date_end": {"gte": date_start}}},
                            {"term": {"is_public_domain": True}},
                        ]
                    }
                },
                "fields": self.fields,
                "limit": min(limit * 2, 25),
            }
            data = _request_json("POST", self.search_url, json_body=body, timeout=10) or {}
            iiif_base = ((data.get("config") or {}).get("iiif_url") or "https://www.artic.edu/iiif/2").rstrip("/")

            for item in data.get("data") or []:
                if len(candidates) >= limit:
                    break
                fetched_count += 1
                item_start = _coerce_int(item.get("date_start"))
                item_end = _coerce_int(item.get("date_end"))
                if not _dates_overlap(item_start, item_end, date_start, date_end):
                    continue

                rec_id = str(item.get("id") or "")
                inv = _clean_text(item.get("main_reference_number"), max_len=100) or (f"AIC-{rec_id}" if rec_id else None)
                ext_url = f"https://www.artic.edu/artworks/{rec_id}" if rec_id else None
                title = _clean_text(item.get("title")) or _clean_text(item.get("artwork_type_title")) or "Untitled Artifact"
                date_disp = _clean_text(item.get("date_display"), max_len=255) or f"{item_start}–{item_end}"

                if index.contains(
                    inventory_number=inv,
                    source_record_id=rec_id,
                    external_url=ext_url,
                    object_type=title,
                    present_location=self.present_location,
                    date_display=date_disp,
                ):
                    duplicates_skipped += 1
                    continue

                parsed = self._parse_record(item, iiif_base, rec_id, inv, title, date_disp, item_start, item_end, kw, ext_url)
                if not parsed["images"]:
                    continue

                index.register(
                    inventory_number=parsed.get("inventory_number"),
                    source_record_id=rec_id,
                    external_url=parsed.get("external_url"),
                    object_type=parsed.get("object_type"),
                    present_location=parsed.get("present_location"),
                    date_display=parsed.get("date_display"),
                )
                candidates.append(parsed)

        return candidates, fetched_count, duplicates_skipped

    def _parse_record(
        self,
        item: Dict[str, Any],
        iiif_base: str,
        rec_id: str,
        inv: Optional[str],
        title: str,
        date_disp: str,
        item_start: Optional[int],
        item_end: Optional[int],
        matched_kw: str,
        ext_url: Optional[str],
    ) -> Dict[str, Any]:
        dims_detail = item.get("dimensions_detail") or []
        first_dim = dims_detail[0] if dims_detail and isinstance(dims_detail[0], dict) else {}
        height = _coerce_float(first_dim.get("height"))
        width = _coerce_float(first_dim.get("width") or first_dim.get("diameter"))
        depth = _coerce_float(first_dim.get("depth"))

        description = strip_html(item.get("description")) or strip_html(item.get("short_description"))
        if not description:
            description = _clean_text(item.get("provenance_text")) or _clean_text(item.get("credit_line"))

        inscr_text = strip_html(item.get("inscriptions"))
        origin = _clean_text(item.get("place_of_origin"), max_len=255)
        medium = _clean_text(item.get("medium_display"), max_len=255)

        citation = (
            f"The Art Institute of Chicago. \"{title}.\" {date_disp}. "
            f"{medium or 'Unknown medium'}. {ext_url or ''}"
        ).strip()

        img_ids: List[str] = []
        if item.get("image_id"):
            img_ids.append(str(item["image_id"]))
        for alt_id in item.get("alt_image_ids") or []:
            if len(img_ids) >= 3:
                break
            if alt_id and str(alt_id) not in img_ids:
                img_ids.append(str(alt_id))

        images = []
        for seq, img_id in enumerate(img_ids, start=1):
            candidate_url = f"{iiif_base}/{img_id}/full/843,/0/default.jpg"
            if not is_safe_image_url(candidate_url):
                continue
            images.append({
                "file_url": candidate_url,
                "image_type": "Colour photo",
                "view_type": "Front" if seq == 1 else f"View {seq}",
                "image_sequence": len(images) + 1,
                "source_identifier": f"AIC {inv or rec_id}" if seq == 1 else f"AIC {inv or rec_id} (alt {seq})",
                "source_citation": citation,
            })

        raw_tags = list((item.get("term_titles") or [])[:8])
        raw_tags.extend([item.get("style_title"), item.get("artwork_type_title"), matched_kw])

        return _finalize_candidate({
            "museum_id": self.museum_id,
            "museum_name": self.museum_name,
            "source_record_id": rec_id,
            "matched_keyword": matched_kw,
            "object_type": title[:255],
            "material": medium,
            "findspot": origin,
            "production_location": origin,
            "present_location": self.present_location,
            "inventory_number": inv,
            "description": description,
            "date_display": date_disp,
            "date_start": item_start if item_start is not None else item_end or 0,
            "date_end": item_end if item_end is not None else item_start or 0,
            "date_basis": _clean_text(item.get("style_title")),
            "width": width,
            "height": height,
            "depth": depth,
            "unit": "cm",
            "dimensions_display": _clean_text(item.get("dimensions"), max_len=255),
            "weight": None,
            "completeness": infer_completeness(title, description),
            "inscription_present": True if inscr_text else None,
            "inscription_1": inscr_text,
            "inscription_2": None,
            "object_group": _clean_text(item.get("artwork_type_title"), max_len=255),
            "publications": strip_html(item.get("publication_history")),
            "external_url": ext_url,
            "tags": raw_tags,
            "images": images,
        })


class VamMuseumAdapter:
    """Adapter for the Victoria and Albert Museum API v2."""

    museum_id: MuseumKey = "vam"
    museum_name = "Victoria and Albert Museum"
    present_location = "Victoria and Albert Museum, London"
    search_url = "https://api.vam.ac.uk/v2/objects/search"
    detail_url = "https://api.vam.ac.uk/v2/museumobject"

    def discover(
        self,
        keywords: List[str],
        date_start: int,
        date_end: int,
        limit: int,
        index: ExistingArtifactIndex,
    ) -> Tuple[List[Dict[str, Any]], int, int]:
        candidates: List[Dict[str, Any]] = []
        fetched_count = 0
        duplicates_skipped = 0
        queued: List[Tuple[str, str]] = []
        seen_sys: Set[str] = set()
        detail_cap = min(limit * 3, 30)

        for kw in keywords:
            if len(queued) >= detail_cap:
                break
            data = _request_json(
                "GET",
                self.search_url,
                params={
                    "q": kw,
                    "year_made_from": date_start,
                    "year_made_to": date_end,
                    "images_exist": 1,
                    "page_size": min(limit * 2, 25),
                },
                timeout=10,
            ) or {}
            for rec in data.get("records") or []:
                sn = rec.get("systemNumber")
                if not sn or sn in seen_sys:
                    continue
                seen_sys.add(sn)
                acc = _clean_text(rec.get("accessionNumber"), max_len=100)
                if index.contains(inventory_number=acc, source_record_id=sn):
                    fetched_count += 1
                    duplicates_skipped += 1
                    continue
                queued.append((sn, kw))
                if len(queued) >= detail_cap:
                    break

        for sn, matched_kw in queued:
            if len(candidates) >= limit:
                break
            detail = _request_json("GET", f"{self.detail_url}/{sn}", timeout=8, allow_404=True)
            if not detail or not isinstance(detail.get("record"), dict):
                continue
            fetched_count += 1
            rec = detail["record"]

            item_start, item_end, date_disp, date_basis = self._parse_dates(rec)
            if not _dates_overlap(item_start, item_end, date_start, date_end):
                continue

            inv = _clean_text(rec.get("accessionNumber"), max_len=100) or sn
            ext_url = f"https://collections.vam.ac.uk/item/{sn}"
            titles = rec.get("titles") or []
            primary_title = (
                _clean_text(titles[0].get("title")) if titles and isinstance(titles[0], dict) else None
            )
            title = primary_title or _clean_text(rec.get("objectType")) or "Untitled Artifact"

            if index.contains(
                inventory_number=inv,
                source_record_id=sn,
                external_url=ext_url,
                object_type=title,
                present_location=self.present_location,
                date_display=date_disp,
            ):
                duplicates_skipped += 1
                continue

            parsed = self._parse_record(rec, sn, inv, title, date_disp, item_start, item_end, date_basis, matched_kw, ext_url)
            if not parsed["images"]:
                continue

            index.register(
                inventory_number=parsed.get("inventory_number"),
                source_record_id=sn,
                external_url=parsed.get("external_url"),
                object_type=parsed.get("object_type"),
                present_location=parsed.get("present_location"),
                date_display=parsed.get("date_display"),
            )
            candidates.append(parsed)

        return candidates, fetched_count, duplicates_skipped

    @staticmethod
    def _parse_iso_year(raw: Any) -> Optional[int]:
        if not raw:
            return None
        match = re.match(r"^\s*(-?\d+)", str(raw))
        return int(match.group(1)) if match else None

    def _parse_dates(self, rec: Dict[str, Any]) -> Tuple[Optional[int], Optional[int], str, Optional[str]]:
        prod_dates = rec.get("productionDates") or []
        if prod_dates and isinstance(prod_dates[0], dict):
            date_obj = prod_dates[0].get("date") or {}
            assoc_obj = prod_dates[0].get("association") or {}
            earliest = self._parse_iso_year(date_obj.get("earliest"))
            latest = self._parse_iso_year(date_obj.get("latest"))
            text = _clean_text(date_obj.get("text"), max_len=255) or f"{earliest}–{latest}"
            basis = _clean_text(assoc_obj.get("text"))
            return earliest, latest, text, basis
        return None, None, "Unknown", None

    def _parse_record(
        self,
        rec: Dict[str, Any],
        sn: str,
        inv: str,
        title: str,
        date_disp: str,
        item_start: Optional[int],
        item_end: Optional[int],
        date_basis: Optional[str],
        matched_kw: str,
        ext_url: str,
    ) -> Dict[str, Any]:
        findspot = None
        production_location = None
        for po in rec.get("placesOfOrigin") or []:
            if not isinstance(po, dict):
                continue
            place_name = _clean_text((po.get("place") or {}).get("text"), max_len=255)
            assoc = ((po.get("association") or {}).get("text") or "").lower()
            if not place_name:
                continue
            if "found" in assoc or "excavat" in assoc:
                findspot = findspot or place_name
            elif "made" in assoc or "manufactur" in assoc or "produc" in assoc:
                production_location = production_location or place_name
            else:
                production_location = production_location or place_name

        if not findspot and production_location:
            findspot = production_location

        height = width = depth = None
        weight = None
        unit = "cm"
        dim_notes = []
        for d in rec.get("dimensions") or []:
            if not isinstance(d, dict):
                continue
            dim_name = (d.get("dimension") or "").lower()
            dim_val = _coerce_float(d.get("value"))
            dim_unit = _clean_text(d.get("unit")) or "cm"
            if d.get("value"):
                dim_notes.append(f"{d.get('dimension')}: {d.get('value')} {dim_unit}".strip())
            if dim_name == "height" and height is None:
                height = dim_val
                unit = dim_unit
            elif dim_name in ("width", "diameter") and width is None:
                width = dim_val
            elif dim_name == "depth" and depth is None:
                depth = dim_val
            elif dim_name == "weight" and weight is None and d.get("value"):
                weight = f"{d.get('value')} {dim_unit}".strip()

        inscr_texts = []
        for m in rec.get("marksAndInscriptions") or []:
            if isinstance(m, dict):
                txt = _clean_text(m.get("content") or m.get("description") or m.get("text"))
                if txt:
                    inscr_texts.append(txt)

        bib_refs = []
        for b in rec.get("bibliographicReferences") or []:
            if isinstance(b, dict):
                txt = _clean_text(b.get("free") or (b.get("reference") or {}).get("text"))
                if txt:
                    bib_refs.append(txt)

        summary = strip_html(rec.get("summaryDescription"))
        physical = strip_html(rec.get("physicalDescription"))
        description = " ".join(p for p in (summary, physical) if p) or None

        medium = _clean_text(rec.get("materialsAndTechniques"), max_len=255)
        citation = (
            f"Victoria and Albert Museum. \"{title}.\" {date_disp}. "
            f"{medium or 'Unknown medium'}. {ext_url}"
        ).strip()

        images = []
        for seq, img_id in enumerate((rec.get("images") or [])[:3], start=1):
            img_url = f"https://framemark.vam.ac.uk/collections/{img_id}/full/!800,800/0/default.jpg"
            if not is_safe_image_url(img_url):
                continue
            images.append({
                "file_url": img_url,
                "image_type": "Colour photo",
                "view_type": "Front" if seq == 1 else f"View {seq}",
                "image_sequence": len(images) + 1,
                "source_identifier": f"V&A {sn} / {img_id}",
                "source_citation": citation,
            })

        tags: List[Optional[str]] = [
            c.get("text") for c in (rec.get("categories") or []) if isinstance(c, dict)
        ]
        tags.extend(m.get("text") for m in (rec.get("materials") or []) if isinstance(m, dict))
        tags.extend(s.get("text") for s in (rec.get("styles") or []) if isinstance(s, dict))
        tags.extend([rec.get("objectType"), matched_kw])

        return _finalize_candidate({
            "museum_id": self.museum_id,
            "museum_name": self.museum_name,
            "source_record_id": sn,
            "matched_keyword": matched_kw,
            "object_type": title[:255],
            "material": medium,
            "findspot": findspot,
            "production_location": production_location,
            "present_location": self.present_location,
            "inventory_number": inv,
            "description": description,
            "date_display": date_disp,
            "date_start": item_start if item_start is not None else item_end or 0,
            "date_end": item_end if item_end is not None else item_start or 0,
            "date_basis": date_basis,
            "width": width,
            "height": height,
            "depth": depth,
            "unit": unit[:20],
            "dimensions_display": _clean_text(rec.get("dimensionsNote") or "; ".join(dim_notes), max_len=255),
            "weight": weight[:100] if weight else None,
            "completeness": infer_completeness(title, description),
            "inscription_present": True if inscr_texts else None,
            "inscription_1": inscr_texts[0] if len(inscr_texts) > 0 else None,
            "inscription_2": inscr_texts[1] if len(inscr_texts) > 1 else None,
            "object_group": _clean_text(rec.get("collectionCode"), max_len=255),
            "publications": "; ".join(bib_refs) if bib_refs else None,
            "external_url": ext_url,
            "tags": tags,
            "images": images,
        })


ADAPTERS: Dict[MuseumKey, Any] = {
    "met": MetMuseumAdapter(),
    "cma": ClevelandMuseumAdapter(),
    "aic": ArtInstituteChicagoAdapter(),
    "vam": VamMuseumAdapter(),
}


class MuseumDiscoveryService:
    """Orchestrates discovery searches and duplicate-safe imports into the Review Queue."""

    def __init__(self, db: Session):
        self.db = db

    def get_saved_keywords(self) -> List[str]:
        """Return persisted discovery keywords ordered by creation, bootstrapping defaults if empty."""
        rows = self.db.query(DiscoveryKeyword).order_by(DiscoveryKeyword.id.asc()).all()
        if not rows:
            for default_kw in DEFAULT_KEYWORDS:
                self.db.add(DiscoveryKeyword(keyword=default_kw, is_default=True))
            try:
                self.db.commit()
            except IntegrityError:
                self.db.rollback()
            rows = self.db.query(DiscoveryKeyword).order_by(DiscoveryKeyword.id.asc()).all()
        return [row.keyword for row in rows]

    def add_keyword(self, raw_keyword: str) -> Dict[str, Any]:
        """Persist a new discovery keyword case-insensitively with bounded capacity."""
        self.get_saved_keywords()
        clean = _clean_text(raw_keyword)
        if not clean or len(clean) > 80:
            raise ValidationError("Keyword must be between 1 and 80 characters.")

        existing = (
            self.db.query(DiscoveryKeyword)
            .filter(func.lower(DiscoveryKeyword.keyword) == clean.lower())
            .first()
        )
        if existing:
            return {
                "keyword": existing.keyword,
                "keywords": self.get_saved_keywords(),
                "created": False,
            }

        current_count = self.db.query(func.count(DiscoveryKeyword.id)).scalar() or 0
        if current_count >= MAX_SAVED_KEYWORDS:
            raise ValidationError(f"Maximum of {MAX_SAVED_KEYWORDS} saved keywords reached.")

        self.db.add(DiscoveryKeyword(keyword=clean, is_default=False))
        try:
            self.db.commit()
            created = True
            saved_kw = clean
        except IntegrityError:
            self.db.rollback()
            created = False
            fallback = (
                self.db.query(DiscoveryKeyword)
                .filter(func.lower(DiscoveryKeyword.keyword) == clean.lower())
                .first()
            )
            saved_kw = fallback.keyword if fallback else clean

        return {
            "keyword": saved_kw,
            "keywords": self.get_saved_keywords(),
            "created": created,
        }

    def save_keywords(self, keywords: List[str]) -> List[str]:
        """Idempotently persist any new keywords used in a discovery search."""
        existing_words = self.get_saved_keywords()
        existing_lower = {kw.lower() for kw in existing_words}
        current_count = len(existing_words)
        added_any = False

        for raw in keywords:
            clean = _clean_text(raw)
            if not clean or len(clean) > 80 or clean.lower() in existing_lower:
                continue
            if current_count >= MAX_SAVED_KEYWORDS:
                break
            self.db.add(DiscoveryKeyword(keyword=clean, is_default=False))
            existing_lower.add(clean.lower())
            current_count += 1
            added_any = True

        if added_any:
            try:
                self.db.commit()
            except IntegrityError:
                self.db.rollback()

        return self.get_saved_keywords()

    def delete_keyword(self, raw_keyword: str) -> bool:
        """Remove a saved discovery keyword case-insensitively."""
        clean = _clean_text(raw_keyword)
        if not clean:
            return False
        existing = (
            self.db.query(DiscoveryKeyword)
            .filter(func.lower(DiscoveryKeyword.keyword) == clean.lower())
            .first()
        )
        if not existing:
            return False
        self.db.delete(existing)
        self.db.commit()
        return True

    def list_museums(self) -> List[Dict[str, Any]]:
        """Return predefined museum specifications with persisted discovery keywords."""
        saved_keywords = self.get_saved_keywords()
        return [{**museum, "default_keywords": list(saved_keywords)} for museum in PREDEFINED_MUSEUMS]

    def discover(self, request: DiscoverySearchRequest) -> Dict[str, Any]:
        """Persist new search keywords, query selected predefined museums, and skip duplicates."""
        self.save_keywords(request.keywords)
        index = ExistingArtifactIndex(self.db)
        all_candidates: List[Dict[str, Any]] = []
        reports: List[Dict[str, Any]] = []
        total_duplicates = 0

        for museum_id in request.museums:
            adapter = ADAPTERS[museum_id]
            try:
                found, fetched, dupes = adapter.discover(
                    keywords=request.keywords,
                    date_start=request.date_start,
                    date_end=request.date_end,
                    limit=request.limit_per_museum,
                    index=index,
                )
                all_candidates.extend(found)
                total_duplicates += dupes
                reports.append({
                    "museum_id": museum_id,
                    "museum_name": adapter.museum_name,
                    "fetched_count": fetched,
                    "new_count": len(found),
                    "duplicates_skipped": dupes,
                    "error": None,
                })
            except Exception as exc:
                app_logger.warning(
                    "Museum discovery failed for %s: %s",
                    museum_id,
                    exc,
                    exc_info=True,
                )
                reports.append({
                    "museum_id": museum_id,
                    "museum_name": adapter.museum_name,
                    "fetched_count": 0,
                    "new_count": 0,
                    "duplicates_skipped": 0,
                    "error": f"Failed querying {adapter.museum_name}: {exc}",
                })

        all_candidates.sort(key=lambda c: ((c.get("object_type") or "").lower(), c.get("museum_id", "")))
        return {
            "candidates": all_candidates,
            "total_new": len(all_candidates),
            "total_duplicates_skipped": total_duplicates,
            "museum_reports": reports,
        }

    def _get_or_create_source(self, citation_text: str) -> Source:
        clean = citation_text.strip()
        existing = self.db.query(Source).filter(Source.citation_text == clean).first()
        if existing:
            return existing
        source = Source(citation_text=clean)
        self.db.add(source)
        self.db.flush()
        return source

    def _get_or_create_tag(self, tag_name: str) -> Tag:
        clean = tag_name.strip()
        existing = self.db.query(Tag).filter(func.lower(Tag.tag_name) == clean.lower()).first()
        if existing:
            return existing
        tag = Tag(tag_name=clean)
        self.db.add(tag)
        self.db.flush()
        return tag

    def import_candidates(self, candidates: List[DiscoveryCandidate]) -> Dict[str, Any]:
        """Persist selected non-duplicate candidates as pending review objects."""
        index = ExistingArtifactIndex(self.db)
        imported_objects: List[Dict[str, Any]] = []
        skipped_inventory_numbers: List[str] = []
        errors: List[str] = []
        duplicates_skipped = 0
        failed_count = 0

        storage_configured = bool(config.MINIO_ENDPOINT and config.MINIO_ACCESS_KEY)

        for cand in candidates:
            if index.contains(
                inventory_number=cand.inventory_number,
                source_record_id=cand.source_record_id,
                external_url=cand.external_url,
                object_type=cand.object_type,
                present_location=cand.present_location,
                date_display=cand.date_display,
            ):
                duplicates_skipped += 1
                if cand.inventory_number:
                    skipped_inventory_numbers.append(cand.inventory_number)
                continue

            try:
                with self.db.begin_nested():
                    db_obj = Object(
                        object_type=cand.object_type[:255],
                        material=cand.material[:255] if cand.material else None,
                        findspot=cand.findspot[:255] if cand.findspot else None,
                        present_location=cand.present_location[:255] if cand.present_location else None,
                        production_location=cand.production_location[:255] if cand.production_location else None,
                        latitude=cand.latitude,
                        longitude=cand.longitude,
                        inventory_number=cand.inventory_number[:100] if cand.inventory_number else None,
                        description=cand.description,
                        date_display=cand.date_display[:255],
                        date_start=cand.date_start,
                        date_end=cand.date_end,
                        date_basis=cand.date_basis,
                        width=cand.width,
                        height=cand.height,
                        depth=cand.depth,
                        unit=(cand.unit or "cm")[:20],
                        dimensions_display=cand.dimensions_display[:255] if cand.dimensions_display else None,
                        weight=cand.weight[:100] if cand.weight else None,
                        completeness=cand.completeness[:255] if cand.completeness else None,
                        inscription_present=cand.inscription_present,
                        inscription_1=cand.inscription_1,
                        inscription_2=cand.inscription_2,
                        object_group=cand.object_group[:255] if cand.object_group else None,
                        publications=cand.publications,
                        external_url=cand.external_url[:500] if cand.external_url else None,
                        review_status="pending",
                    )
                    self.db.add(db_obj)
                    self.db.flush()

                    primary_img_record: Optional[Image] = None
                    for seq, img_in in enumerate(cand.images[:3], start=1):
                        stored_url = ""
                        if img_in.file_url and storage_configured:
                            cached = download_and_store_image(
                                img_in.file_url,
                                object_identifier=cand.inventory_number or db_obj.id,
                                prefix=cand.museum_id,
                            )
                            if cached:
                                stored_url = cached
                            else:
                                app_logger.warning(
                                    "Could not cache image into bucket for %s; storing empty placeholder URL",
                                    cand.inventory_number or db_obj.id,
                                )

                        source_id = None
                        if img_in.source_citation and img_in.source_citation.strip():
                            source = self._get_or_create_source(img_in.source_citation)
                            source_id = source.id

                        db_img = Image(
                            object_id=db_obj.id,
                            source_id=source_id,
                            image_type=(img_in.image_type or "Colour photo")[:50],
                            view_type=(img_in.view_type or "Full")[:50],
                            image_sequence=img_in.image_sequence or seq,
                            source_identifier=img_in.source_identifier[:255] if img_in.source_identifier else None,
                            file_url=stored_url,
                        )
                        self.db.add(db_img)
                        if primary_img_record is None:
                            primary_img_record = db_img

                    self.db.flush()
                    if primary_img_record is not None and cand.tags:
                        attached_lower: Set[str] = set()
                        for raw_tag in cand.tags:
                            clean_tag = raw_tag.strip()
                            if not clean_tag or clean_tag.lower() in attached_lower:
                                continue
                            attached_lower.add(clean_tag.lower())
                            tag_model = self._get_or_create_tag(clean_tag)
                            if tag_model not in primary_img_record.tags:
                                primary_img_record.tags.append(tag_model)

                index.register(
                    inventory_number=cand.inventory_number,
                    source_record_id=cand.source_record_id,
                    external_url=cand.external_url,
                    object_type=cand.object_type,
                    present_location=cand.present_location,
                    date_display=cand.date_display,
                )
                imported_objects.append({
                    "id": db_obj.id,
                    "object_type": db_obj.object_type,
                    "inventory_number": db_obj.inventory_number,
                    "present_location": db_obj.present_location,
                    "review_status": db_obj.review_status,
                })
            except IntegrityError:
                duplicates_skipped += 1
                if cand.inventory_number:
                    skipped_inventory_numbers.append(cand.inventory_number)
            except Exception as exc:
                failed_count += 1
                app_logger.warning("Failed importing candidate %s: %s", cand.inventory_number, exc, exc_info=True)
                errors.append(f"Failed importing '{cand.object_type}': {exc}")

        self.db.commit()
        return {
            "imported_count": len(imported_objects),
            "duplicates_skipped": duplicates_skipped,
            "failed_count": failed_count,
            "imported_objects": imported_objects,
            "skipped_inventory_numbers": skipped_inventory_numbers,
            "errors": errors,
        }
