# Database Design - Academic Artifact Research

This document outlines the architectural logic and design decisions for the Academic Artifact Research Database. The system is designed to support the storage and retrieval of historical artifact data with a focus on high cohesion, low coupling, and specialized handling for historical uncertainties.

## 1. Database Architecture Logic

### Core Strategy: Object vs. Image Separation
We maintain a strict separation between **Objects** (physical artifacts) and **Images** (digital representations). 
- **Objects:** Represent the physical entity (e.g., a vase, a coin). This table holds attributes intrinsic to the item itself.
- **Images:** Represent digital files depicting the object. One Object can have many Images (1:N relationship).
- **Benefit:** This prevents data duplication. Metadata about the physical object is stored once, regardless of how many photos or scans exist of it.

### Scalability: External File Storage
- **No BLOBs:** Images are **NOT** stored directly in the database as BLOBs (Binary Large Objects).
- **Reference Storage:** The `images` table stores a specific `file_url` pointing to an external object storage service (AWS S3).
- **Benefit:** Keeps the database lightweight and performant. Database backups are smaller and faster. Scaling storage for terabytes of high-resolution images is handled by S3, which is more cost-effective and efficient than database storage.

### Fuzzy Dates: 3-Column Approach
Historical artifacts often have uncertain dating (e.g., "c. 4th Century", "Late Bronze Age"). A standard `DATE` type is insufficient. We use a 3-column approach:
1.  **`date_display` (VARCHAR):** The human-readable string presented to the user (e.g., "c. 350-400 AD").
2.  **`date_start` (INTEGER):** The earliest possible year representing the start of the range (e.g., `350`).
3.  **`date_end` (INTEGER):** The latest possible year representing the end of the range (e.g., `400`).
- **Benefit:** Allows for precise range queries (e.g., "Find all objects that existed between 300 and 500") while preserving the scholarly nuance of the date description.

### Map Visualization
- The `objects` table includes `latitude` and `longitude` columns (DECIMAL/FLOAT).
- **Benefit:** Directly supports the required Map UI, allowing users to visualize the geographical distribution of `findspot` locations without needing complex joins or external geocoding services at runtime.

## 2. Schema Overview

The schema consists of the following noramlized tables:

- **`objects`**: The central entity table.
- **`sources`**: Bibliographic references.
- **`images`**: Digital assets linked to objects and sources.
- **`tags`**: Controlled vocabulary for categorization.
- **`image_tags`**: Many-to-Many junction table linking images to tags.

Refer to `code/backend/database_schema.sql` for the complete SQL DDL implementation.
