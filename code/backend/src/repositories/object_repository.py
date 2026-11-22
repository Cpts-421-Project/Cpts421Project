from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text, or_, func, case
from typing import List, Optional
from ..models import Object, Image, Source, Tag
from ..schemas import ObjectDetailResponse, ObjectMapResponse

UPDATABLE_OBJECT_FIELDS = frozenset({
    "object_type",
    "material",
    "findspot",
    "date_display",
    "date_start",
    "date_end",
    "inventory_number",
    "latitude",
    "longitude",
    "description",
    "width",
    "height",
    "depth",
    "unit",
    "dimensions_display",
    "weight",
    "completeness",
    "date_basis",
    "present_location",
    "production_location",
    "object_group",
    "inscription_present",
    "inscription_1",
    "inscription_2",
    "publications",
    "caption",
    "external_url",
    "review_status",
})

UPDATABLE_IMAGE_FIELDS = frozenset({
    "file_url",
    "image_type",
    "view_type",
    "image_sequence",
    "source_identifier",
    "source_id",
})


class ObjectRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Object]:
        return self.db.query(Object).options(
            joinedload(Object.images).joinedload(Image.source),
            joinedload(Object.images).joinedload(Image.tags),
        ).offset(skip).limit(limit).all()

    def get_by_id(self, object_id: int) -> Optional[Object]:
        """Fetch a single object by primary key. Returns None if not found."""
        return self.db.query(Object).options(
            joinedload(Object.images).joinedload(Image.source),
            joinedload(Object.images).joinedload(Image.tags),
        ).filter(Object.id == object_id).first()

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
    ) -> List[Object]:
        if object_ids is not None and len(object_ids) == 0:
            return []

        query = self.db.query(Object).options(
            joinedload(Object.images).joinedload(Image.source),
            joinedload(Object.images).joinedload(Image.tags),
        ).filter(Object.review_status == 'accepted')

        if object_ids is not None:
            query = query.filter(Object.id.in_(object_ids))

        # General text search across core metadata, scholarly fields, and tags
        if search and search.strip():
            term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Object.object_type.ilike(term),
                    Object.description.ilike(term),
                    Object.material.ilike(term),
                    Object.findspot.ilike(term),
                    Object.present_location.ilike(term),
                    Object.production_location.ilike(term),
                    Object.object_group.ilike(term),
                    Object.publications.ilike(term),
                    Object.inscription_1.ilike(term),
                    Object.inscription_2.ilike(term),
                    Object.completeness.ilike(term),
                    Object.date_basis.ilike(term),
                    Object.inventory_number.ilike(term),
                    Object.images.any(Image.tags.any(Tag.tag_name.ilike(term))),
                )
            )

        if material and material.strip():
            query = query.filter(Object.material.ilike(f"%{material.strip()}%"))

        # Tag-based filtering
        if tags:
            valid_tags = [t.strip() for t in tags if t and t.strip()]
            if valid_tags:
                if tag_mode == "all":
                    for t in valid_tags:
                        query = query.filter(
                            Object.images.any(
                                Image.tags.any(func.lower(Tag.tag_name) == t.lower())
                            )
                        )
                else:  # default: "any" (matches objects containing any of the selected tags)
                    query = query.filter(
                        Object.images.any(
                            Image.tags.any(
                                or_(*[func.lower(Tag.tag_name) == t.lower() for t in valid_tags])
                            )
                        )
                    )

        if year is not None:
            query = query.filter(Object.date_start <= year, Object.date_end >= year)
        
        if date_start is not None:
            query = query.filter(Object.date_end >= date_start)
        if date_end is not None:
            query = query.filter(Object.date_start <= date_end)

        is_desc = sort_order == "desc"
        if sort_by == "date":
            start_col = Object.date_start.desc() if is_desc else Object.date_start.asc()
            end_col = Object.date_end.desc() if is_desc else Object.date_end.asc()
            query = query.order_by(
                start_col,
                end_col,
                func.lower(Object.object_type).asc(),
                Object.id.asc(),
            )
        elif sort_by == "location":
            loc_expr = func.coalesce(
                func.nullif(Object.findspot, ""),
                func.nullif(Object.production_location, ""),
                func.nullif(Object.present_location, ""),
            )
            null_rank = case((loc_expr.is_(None), 1), else_=0).asc()
            loc_col = func.lower(loc_expr).desc() if is_desc else func.lower(loc_expr).asc()
            query = query.order_by(
                null_rank,
                loc_col,
                func.lower(Object.object_type).asc(),
                Object.id.asc(),
            )
        elif sort_by == "material":
            mat_expr = func.nullif(Object.material, "")
            null_rank = case((mat_expr.is_(None), 1), else_=0).asc()
            mat_col = func.lower(mat_expr).desc() if is_desc else func.lower(mat_expr).asc()
            query = query.order_by(
                null_rank,
                mat_col,
                func.lower(Object.object_type).asc(),
                Object.id.asc(),
            )
        else:  # Default: alphabetical by title
            title_col = func.lower(Object.object_type).desc() if is_desc else func.lower(Object.object_type).asc()
            query = query.order_by(title_col, Object.id.asc())

        results = query.offset(skip).limit(limit).all()
        return results


    def get_map_data(self) -> List[dict]:
        # Return lightweight data with findspot for map cluster labels
        objects = (
            self.db.query(Object.id, Object.object_type, Object.findspot, Object.latitude, Object.longitude)
            .filter(Object.review_status == 'accepted')
            .all()
        )
        return [
            {
                "id": obj.id,
                "name": obj.object_type,
                "findspot": obj.findspot,
                "latitude": obj.latitude,
                "longitude": obj.longitude,
            }
            for obj in objects
        ]

    def get_all_tags(self) -> List[str]:
        """Fetch all unique tag names sorted alphabetically (case-insensitive)."""
        tags = self.db.query(Tag.tag_name).distinct().all()
        return sorted({tag[0] for tag in tags if tag[0]}, key=lambda t: (t.lower(), t))
        
    def get_pending_objects(self) -> List[Object]:
        """Fetch all objects awaiting admin review."""
        return self.db.query(Object).options(
            joinedload(Object.images).joinedload(Image.source)
        ).filter(Object.review_status == 'pending').order_by(Object.id.asc()).limit(50).all()

    def _get_or_create_source_id(self, citation_text: str) -> int:
        clean_citation = citation_text.strip()
        existing = self.db.query(Source).filter(Source.citation_text == clean_citation).first()
        if existing:
            return existing.id
        source = Source(citation_text=clean_citation)
        self.db.add(source)
        self.db.flush()
        return source.id

    def _build_image_model(self, img_data: dict, object_id: int) -> Image:
        payload = dict(img_data)
        citation = payload.pop("source_citation", None)
        if isinstance(citation, str) and citation.strip():
            payload["source_id"] = self._get_or_create_source_id(citation)
        sanitized = {k: v for k, v in payload.items() if k in UPDATABLE_IMAGE_FIELDS}
        return Image(**sanitized, object_id=object_id)

    def add_object(self, obj_data: dict, images_data: Optional[List[dict]] = None) -> Object:
        sanitized_data = {k: v for k, v in obj_data.items() if k in UPDATABLE_OBJECT_FIELDS}
        db_obj = Object(**sanitized_data)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        
        images_list = images_data or []
        for img in images_list:
            db_img = self._build_image_model(img, db_obj.id)
            self.db.add(db_img)
        self.db.commit()
        return self.get_by_id(db_obj.id) or db_obj

    def update_object(self, object_id: int, obj_data: dict, images_data: Optional[List[dict]] = None) -> Optional[Object]:
        db_obj = self.get_by_id(object_id)
        if not db_obj:
            return None
            
        for key, value in obj_data.items():
            if key in UPDATABLE_OBJECT_FIELDS:
                setattr(db_obj, key, value)
            
        if images_data is not None:
            self.db.query(Image).filter(Image.object_id == object_id).delete()
            for img in images_data:
                db_img = self._build_image_model(img, object_id)
                self.db.add(db_img)
            
        self.db.commit()
        self.db.expire(db_obj)
        return self.get_by_id(object_id)

    def delete_object(self, object_id: int) -> bool:
        db_obj = self.get_by_id(object_id)
        if not db_obj:
            return False
        # image deletion cascades via relation
        self.db.delete(db_obj)
        self.db.commit()
        return True
