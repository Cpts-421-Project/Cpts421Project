-- Academic Artifact Research Database Schema (PostgreSQL)
-- Table Definitions and DDL

-- =================================================================================
-- 1. Table Definitions
-- =================================================================================

-- 1.1 SOURCES
-- Represents bibliographic references or origins of data/images.
CREATE TABLE sources (
    id SERIAL PRIMARY KEY,
    citation_text TEXT NOT NULL -- Full citation in Chicago style
);

-- 1.2 OBJECTS
-- Represents physical artifacts.
-- Includes core attributes, fuzzy dating logic, and map coordinates.
CREATE TABLE objects (
    id SERIAL PRIMARY KEY,
    object_type VARCHAR(255) NOT NULL, -- e.g., 'Vase', 'Coin'
    material VARCHAR(255),             -- e.g., 'Gold', 'Clay'
    findspot VARCHAR(255),             -- Original location of discovery
    present_location VARCHAR(255),     -- Collection / repository (e.g., Museum, City)
    production_location VARCHAR(255),  -- Suggested place of manufacture
    latitude DECIMAL(9, 6),            -- For Map UI: -90.0 to 90.0
    longitude DECIMAL(9, 6),           -- For Map UI: -180.0 to 180.0
    date_discovered DATE,              -- Precise date of discovery (if known)
    inventory_number VARCHAR(100) UNIQUE, -- Museum/Collection ID
    description TEXT,                  -- Optional descriptive text about the artifact
    
    -- Fuzzy Dates System (3-Column Approach)
    date_display VARCHAR(255) NOT NULL,-- Display string (e.g., "c. 350-400 AD")
    date_start INTEGER NOT NULL,       -- Start year (Inclusive)
    date_end INTEGER NOT NULL,         -- End year (Inclusive)
    date_basis TEXT,                   -- Basis / discussion of dating
    
    -- Dimensions & Physical Attributes
    width DECIMAL(10, 2),
    height DECIMAL(10, 2),
    depth DECIMAL(10, 2),
    unit VARCHAR(20) DEFAULT 'cm',
    dimensions_display VARCHAR(255),
    weight VARCHAR(100),
    completeness VARCHAR(255),

    -- Inscriptions, Group & Scholarly References
    inscription_present BOOLEAN,
    inscription_1 TEXT,
    inscription_2 TEXT,
    object_group VARCHAR(255),
    publications TEXT,
    caption TEXT,
    external_url VARCHAR(500),
    review_status VARCHAR(50) DEFAULT 'pending'
);

-- Indexes for performance on common filters
CREATE INDEX idx_objects_date_start ON objects(date_start);
CREATE INDEX idx_objects_date_end ON objects(date_end);
CREATE INDEX idx_objects_type ON objects(object_type);
CREATE INDEX idx_objects_present_location ON objects(present_location);

-- 1.3 IMAGES
-- Represents digital files linked to objects.
-- Note: Files are stored externally (e.g., S3), only URLs are stored here.
CREATE TABLE images (
    id SERIAL PRIMARY KEY,
    object_id INTEGER REFERENCES objects(id) ON DELETE CASCADE,
    source_id INTEGER REFERENCES sources(id) ON DELETE SET NULL,
    image_type VARCHAR(50),  -- e.g., 'Photograph', 'Drawing', 'Scan'
    view_type VARCHAR(50),   -- e.g., 'Front', 'Back', 'Detail'
    image_sequence INTEGER,  -- Sub-index within object (e.g., 1 -> 1.1, 2 -> 1.2)
    source_identifier VARCHAR(255), -- Plate/figure number in image source
    file_url TEXT NOT NULL   -- Link to internal storage (/api/images/...)
);

-- 1.4 TAGS
-- A controlled vocabulary for categorizing images/objects.
CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    tag_name VARCHAR(100) UNIQUE NOT NULL
);

-- 1.5 IMAGE_TAGS
-- Many-to-Many relationship between Images and Tags.
CREATE TABLE image_tags (
    image_id INTEGER REFERENCES images(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (image_id, tag_id)
);

CREATE INDEX idx_image_tags_tag_id ON image_tags(tag_id);

-- 1.6 USERS
-- Admins using the system
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE
);

-- 1.7 DISCOVERY_KEYWORDS
-- Persistent saved search keywords for predefined museum discovery
CREATE TABLE discovery_keywords (
    id SERIAL PRIMARY KEY,
    keyword VARCHAR(80) UNIQUE NOT NULL,
    is_default BOOLEAN NOT NULL DEFAULT FALSE
);

-- 1.8 REJECTED_ARTIFACTS
-- Persistent tombstones of rejected museum/review artifacts so future searches skip them
CREATE TABLE rejected_artifacts (
    id SERIAL PRIMARY KEY,
    museum_id VARCHAR(32),
    source_record_id VARCHAR(100),
    inventory_number VARCHAR(100),
    external_url VARCHAR(500),
    object_type VARCHAR(255),
    present_location VARCHAR(255),
    date_display VARCHAR(255),
    rejected_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_rejected_artifacts_museum_id ON rejected_artifacts(museum_id);
CREATE INDEX ix_rejected_artifacts_source_record_id ON rejected_artifacts(source_record_id);
CREATE INDEX ix_rejected_artifacts_inventory_number ON rejected_artifacts(inventory_number);
CREATE INDEX ix_rejected_artifacts_external_url ON rejected_artifacts(external_url);
