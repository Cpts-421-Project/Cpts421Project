from sqlalchemy import Column, Integer, String, Date, DateTime, Numeric, ForeignKey, Table, Boolean, func
from sqlalchemy.orm import relationship
from .database import Base

# Many-to-Many relationship table for Image <-> Tag
image_tags = Table(
    "image_tags",
    Base.metadata,
    Column("image_id", Integer, ForeignKey("images.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False)

class Source(Base):
    __tablename__ = "sources"
    id = Column(Integer, primary_key=True, index=True)
    citation_text = Column(String, nullable=False)

class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True, index=True)
    tag_name = Column(String(100), unique=True, nullable=False)

class Image(Base):
    __tablename__ = "images"
    id = Column(Integer, primary_key=True, index=True)
    object_id = Column(Integer, ForeignKey("objects.id", ondelete="CASCADE"))
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="SET NULL"))
    image_type = Column(String(50))
    view_type = Column(String(50))
    image_sequence = Column(Integer)
    source_identifier = Column(String(255))
    file_url = Column(String, nullable=False)

    # Relationships
    tags = relationship("Tag", secondary=image_tags, backref="images")
    source = relationship("Source")

class Object(Base):
    __tablename__ = "objects"
    id = Column(Integer, primary_key=True, index=True)
    object_type = Column(String(255), nullable=False)
    material = Column(String(255))
    findspot = Column(String(255))
    present_location = Column(String(255), index=True)
    production_location = Column(String(255))
    latitude = Column(Numeric(9, 6))
    longitude = Column(Numeric(9, 6))
    date_discovered = Column(Date)
    inventory_number = Column(String(100), unique=True)
    description = Column(String)
    
    # Fuzzy Dates System
    date_display = Column(String(255), nullable=False)
    date_start = Column(Integer, nullable=False, index=True)
    date_end = Column(Integer, nullable=False, index=True)
    date_basis = Column(String)
    
    # Dimensions & Physical Attributes
    width = Column(Numeric(10, 2))
    height = Column(Numeric(10, 2))
    depth = Column(Numeric(10, 2))
    unit = Column(String(20), default='cm')
    dimensions_display = Column(String(255))
    weight = Column(String(100))
    completeness = Column(String(255))

    # Inscriptions, Group & Scholarly References
    inscription_present = Column(Boolean)
    inscription_1 = Column(String)
    inscription_2 = Column(String)
    object_group = Column(String(255))
    publications = Column(String)
    caption = Column(String)
    external_url = Column(String(500))

    # Review Feature (Admin-only queue)
    review_status = Column(String(50), default="pending", index=True)

    # Relationships
    images = relationship("Image", backref="object", cascade="all, delete-orphan")


class DiscoveryKeyword(Base):
    __tablename__ = "discovery_keywords"
    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(80), unique=True, nullable=False, index=True)
    is_default = Column(Boolean, nullable=False, default=False)


class RejectedArtifact(Base):
    __tablename__ = "rejected_artifacts"
    id = Column(Integer, primary_key=True, index=True)
    museum_id = Column(String(32), index=True)
    source_record_id = Column(String(100), index=True)
    inventory_number = Column(String(100), index=True)
    external_url = Column(String(500), index=True)
    object_type = Column(String(255))
    present_location = Column(String(255))
    date_display = Column(String(255))
    rejected_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

