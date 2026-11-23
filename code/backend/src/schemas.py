import re
from urllib.parse import urlparse
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from typing import Any, List, Optional, Literal
from .services.s3_service import normalize_bucket_url_to_proxy
from .url_validator import is_safe_image_url

class UserLogin(BaseModel):
    username: str
    password: str
    honeypot: Optional[str] = None
    website: Optional[str] = None

class ImageCreate(BaseModel):
    file_url: str = ""
    image_type: Optional[str] = "Photograph"
    view_type: Optional[str] = "Front"
    image_sequence: Optional[int] = None
    source_identifier: Optional[str] = None
    source_citation: Optional[str] = None

class ObjectBase(BaseModel):
    object_type: str
    material: Optional[str] = None
    findspot: Optional[str] = None
    date_display: str
    date_start: int
    date_end: int
    inventory_number: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None
    width: Optional[float] = None
    height: Optional[float] = None
    depth: Optional[float] = None
    unit: Optional[str] = "cm"
    dimensions_display: Optional[str] = None
    weight: Optional[str] = None
    completeness: Optional[str] = None
    date_basis: Optional[str] = None
    present_location: Optional[str] = None
    production_location: Optional[str] = None
    object_group: Optional[str] = None
    inscription_present: Optional[bool] = None
    inscription_1: Optional[str] = None
    inscription_2: Optional[str] = None
    publications: Optional[str] = None
    caption: Optional[str] = None
    external_url: Optional[str] = None

    @field_validator("external_url")
    @classmethod
    def validate_external_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        cleaned = v.strip()
        if not cleaned:
            return None
        parsed = urlparse(cleaned)
        if parsed.scheme.lower() != "https" or not parsed.netloc:
            raise ValueError("external_url must use https:// and include a valid host")
        return cleaned

class ObjectCreate(ObjectBase):
    images: List[ImageCreate] = []

class ObjectUpdate(ObjectBase):
    images: Optional[List[ImageCreate]] = None

class ImageResponse(BaseModel):
    id: int
    image_type: Optional[str]
    view_type: Optional[str]
    file_url: str
    image_sequence: Optional[int] = None
    db_identifier: Optional[str] = None
    source_identifier: Optional[str] = None
    source_citation: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

    @field_validator("file_url", mode="before")
    @classmethod
    def normalize_file_url(cls, v: Any) -> Any:
        if isinstance(v, str):
            v = normalize_bucket_url_to_proxy(v)
            if v.startswith("/api/images/"):
                return v
            v_lower = v.lower()
            if "collectionapi" in v_lower or (
                "metmuseum" in v_lower and ("/iiif/" in v_lower or "www.metmuseum.org" in v_lower)
            ):
                match = re.search(r"/iiif/([^/]+)/", v)
                if match:
                    safe_inv = "".join(c if c.isalnum() else "_" for c in match.group(1))
                    return f"/api/images/met_{safe_inv}.jpg"
                return "/api/images/met_default.jpg"
            if "britishmuseum" in v_lower:
                match = re.search(r"/object/([^/]+)", v)
                if match:
                    safe_inv = "".join(c if c.isalnum() else "_" for c in match.group(1))
                    return f"/api/images/bm_{safe_inv}.jpg"
                return "/api/images/bm_default.jpg"
        return v

class SourceResponse(BaseModel):
    id: int
    citation_text: str
    model_config = ConfigDict(from_attributes=True)

class ObjectMapResponse(BaseModel):
    id: int
    name: str  # Mapping from object_type
    findspot: Optional[str] = None
    latitude: Optional[float]
    longitude: Optional[float]
    model_config = ConfigDict(from_attributes=True)

class ObjectDetailResponse(ObjectBase):
    id: int
    review_status: str = "pending"
    images: List[ImageResponse]
    bibliography: List[str]
    assembled_caption: str = ""
    tags: List[str] = []
    model_config = ConfigDict(from_attributes=True)

class ReviewUpdate(BaseModel):
    status: Literal["accepted", "rejected", "pending"]


MuseumKey = Literal["met", "cma", "aic", "vam", "bm"]
DiscoverySearchMode = Literal["worker_depictions", "broad"]
WorkerConfidence = Literal["high", "medium", "low", "none"]


def _validate_https_url(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    parsed = urlparse(cleaned)
    if parsed.scheme.lower() != "https" or not parsed.netloc:
        raise ValueError("URL must use https:// and include a valid host")
    return cleaned


class PredefinedMuseumResponse(BaseModel):
    id: MuseumKey
    name: str
    present_location: str
    description: str
    default_keywords: List[str]
    default_date_start: int
    default_date_end: int
    default_limit: int


class DiscoveryPresetResponse(BaseModel):
    id: str
    name: str
    description: str
    keywords: List[str]
    recommended_date_start: int
    recommended_date_end: int


_CONTROL_CHAR_RE = re.compile(r"[\x00-\x1f\x7f]")


def _normalize_keyword(raw: Any) -> str:
    """Normalize whitespace and reject control characters or oversized keywords."""
    if not isinstance(raw, str):
        raise ValueError("Keyword must be a string.")
    if _CONTROL_CHAR_RE.search(raw):
        raise ValueError("Keyword contains invalid control characters.")
    cleaned = re.sub(r"\s+", " ", raw).strip()
    if len(cleaned) > 80:
        raise ValueError("Each keyword must be 80 characters or fewer.")
    return cleaned


class DiscoverySearchRequest(BaseModel):
    museums: List[MuseumKey] = Field(min_length=1, max_length=5)
    keywords: List[str] = Field(min_length=1, max_length=200)
    date_start: int = Field(0, ge=-5000, le=2026)
    date_end: int = Field(899, ge=-5000, le=2026)
    limit_per_museum: int = Field(10, ge=1, le=25)
    search_mode: DiscoverySearchMode = "broad"
    min_worker_score: int = Field(35, ge=0, le=100)
    save_keywords: bool = True

    @field_validator("museums")
    @classmethod
    def deduplicate_museums(cls, v: List[MuseumKey]) -> List[MuseumKey]:
        seen = set()
        unique: List[MuseumKey] = []
        for item in v:
            if item not in seen:
                seen.add(item)
                unique.append(item)
        if not unique:
            raise ValueError("At least one museum must be selected.")
        return unique

    @field_validator("keywords")
    @classmethod
    def validate_and_deduplicate_keywords(cls, v: List[str]) -> List[str]:
        seen = set()
        cleaned: List[str] = []
        for raw in v:
            kw = _normalize_keyword(raw) if isinstance(raw, str) else ""
            if not kw:
                continue
            low = kw.lower()
            if low not in seen:
                seen.add(low)
                cleaned.append(kw)
        if not cleaned:
            raise ValueError("At least one non-empty keyword is required.")
        return cleaned

    @model_validator(mode="after")
    def validate_date_bounds(self) -> "DiscoverySearchRequest":
        if self.date_start > self.date_end:
            raise ValueError("date_start must be less than or equal to date_end.")
        return self


class DiscoveryCandidateImage(BaseModel):
    file_url: str = ""
    image_type: Optional[str] = "Colour photo"
    view_type: Optional[str] = "Full"
    image_sequence: int = Field(1, ge=1)
    source_identifier: Optional[str] = None
    source_citation: Optional[str] = None

    @field_validator("file_url")
    @classmethod
    def validate_image_url(cls, v: str) -> str:
        cleaned = (v or "").strip()
        if not cleaned:
            return ""
        if not is_safe_image_url(cleaned):
            raise ValueError(f"Image URL is not in the allowlist: {cleaned}")
        return cleaned


class DiscoveryCandidate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    museum_id: MuseumKey
    museum_name: str
    source_record_id: str
    matched_keyword: Optional[str] = None
    object_type: str
    material: Optional[str] = None
    findspot: Optional[str] = None
    production_location: Optional[str] = None
    present_location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    inventory_number: Optional[str] = None
    description: Optional[str] = None
    date_display: str
    date_start: int
    date_end: int
    date_basis: Optional[str] = None
    width: Optional[float] = None
    height: Optional[float] = None
    depth: Optional[float] = None
    unit: Optional[str] = "cm"
    dimensions_display: Optional[str] = None
    weight: Optional[str] = None
    completeness: Optional[str] = None
    inscription_present: Optional[bool] = None
    inscription_1: Optional[str] = None
    inscription_2: Optional[str] = None
    object_group: Optional[str] = None
    publications: Optional[str] = None
    external_url: Optional[str] = None
    assembled_caption: str = ""
    tags: List[str] = []
    images: List[DiscoveryCandidateImage] = []
    filled_fields_count: int = 0
    worker_relevance_score: int = Field(0, ge=0, le=100)
    worker_confidence: WorkerConfidence = "none"
    worker_signals: List[str] = Field(default_factory=list)

    @field_validator("external_url")
    @classmethod
    def validate_candidate_external_url(cls, v: Optional[str]) -> Optional[str]:
        return _validate_https_url(v)


class MuseumDiscoveryReport(BaseModel):
    museum_id: MuseumKey
    museum_name: str
    fetched_count: int = 0
    new_count: int = 0
    duplicates_skipped: int = 0
    rejected_skipped: int = 0
    filtered_non_worker: int = 0
    error: Optional[str] = None


class DiscoverySearchResponse(BaseModel):
    candidates: List[DiscoveryCandidate]
    total_new: int
    total_duplicates_skipped: int
    total_rejected_skipped: int = 0
    total_filtered_non_worker: int = 0
    search_mode: DiscoverySearchMode = "broad"
    museum_reports: List[MuseumDiscoveryReport]


class DiscoveryImportRequest(BaseModel):
    candidates: List[DiscoveryCandidate] = Field(min_length=1, max_length=100)


class DiscoveryRejectItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    museum_id: MuseumKey
    source_record_id: str = Field(..., min_length=1, max_length=100)
    inventory_number: Optional[str] = Field(None, max_length=100)
    external_url: Optional[str] = Field(None, max_length=500)
    object_type: Optional[str] = Field(None, max_length=255)
    present_location: Optional[str] = Field(None, max_length=255)
    date_display: Optional[str] = Field(None, max_length=255)

    @field_validator("source_record_id")
    @classmethod
    def validate_source_record_id(cls, v: str) -> str:
        if _CONTROL_CHAR_RE.search(v):
            raise ValueError("source_record_id contains invalid control characters.")
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("source_record_id cannot be empty.")
        return cleaned

    @field_validator("inventory_number", "object_type", "present_location", "date_display")
    @classmethod
    def sanitize_optional_text(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        if _CONTROL_CHAR_RE.search(v):
            raise ValueError("Field contains invalid control characters.")
        cleaned = re.sub(r"\s+", " ", v).strip()
        return cleaned or None

    @field_validator("external_url")
    @classmethod
    def validate_reject_external_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        if _CONTROL_CHAR_RE.search(v):
            raise ValueError("external_url contains invalid control characters.")
        return _validate_https_url(v)


class DiscoveryRejectRequest(BaseModel):
    candidates: List[DiscoveryRejectItem] = Field(min_length=1, max_length=100)


class RejectedArtifactItem(BaseModel):
    id: int
    museum_id: Optional[str] = None
    source_record_id: Optional[str] = None
    inventory_number: Optional[str] = None
    external_url: Optional[str] = None
    object_type: Optional[str] = None
    present_location: Optional[str] = None
    date_display: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class DiscoveryRejectResponse(BaseModel):
    rejected_count: int
    already_rejected_count: int
    rejected_items: List[RejectedArtifactItem]


class DiscoveryImportedItem(BaseModel):
    id: int
    object_type: str
    inventory_number: Optional[str] = None
    present_location: Optional[str] = None
    review_status: str = "pending"


class DiscoveryImportResponse(BaseModel):
    imported_count: int
    duplicates_skipped: int
    failed_count: int
    imported_objects: List[DiscoveryImportedItem]
    skipped_inventory_numbers: List[str] = []
    errors: List[str] = []


class DiscoveryKeywordCreate(BaseModel):
    keyword: str = Field(..., min_length=1, max_length=80)

    @field_validator("keyword")
    @classmethod
    def validate_keyword(cls, v: str) -> str:
        cleaned = _normalize_keyword(v)
        if not cleaned:
            raise ValueError("Keyword cannot be empty.")
        return cleaned


class DiscoveryKeywordResponse(BaseModel):
    keyword: str
    keywords: List[str]
    created: bool
