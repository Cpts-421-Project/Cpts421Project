import re
from pydantic import BaseModel, ConfigDict, field_validator
from typing import Any, List, Optional, Literal

class UserLogin(BaseModel):
    username: str
    password: str

class ImageCreate(BaseModel):
    file_url: str
    image_type: Optional[str] = "Photograph"
    view_type: Optional[str] = "Front"

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

class ObjectCreate(ObjectBase):
    images: List[ImageCreate] = []

class ObjectUpdate(ObjectBase):
    images: List[ImageCreate] = []

class ImageResponse(BaseModel):
    id: int
    image_type: Optional[str]
    view_type: Optional[str]
    file_url: str
    model_config = ConfigDict(from_attributes=True)

    @field_validator("file_url", mode="before")
    @classmethod
    def normalize_file_url(cls, v: Any) -> Any:
        if isinstance(v, str):
            v_lower = v.lower()
            if "metmuseum" in v_lower or "collectionapi" in v_lower:
                match = re.search(r"/iiif/([^/]+)/", v)
                if match:
                    safe_inv = "".join(c if c.isalnum() else "_" for c in match.group(1))
                    return f"/api/images/met_{safe_inv}.jpg"
                return "/api/images/met_default.jpg"
        return v

class SourceResponse(BaseModel):
    id: int
    citation_text: str
    model_config = ConfigDict(from_attributes=True)

class ObjectMapResponse(BaseModel):
    id: int
    name: str  # Mapping from object_type
    latitude: Optional[float]
    longitude: Optional[float]
    model_config = ConfigDict(from_attributes=True)

class ObjectDetailResponse(ObjectBase):
    id: int
    review_status: str = "pending"
    images: List[ImageResponse]
    bibliography: List[str]
    tags: List[str] = []
    model_config = ConfigDict(from_attributes=True)

class ReviewUpdate(BaseModel):
    status: Literal["accepted", "rejected", "pending"]
